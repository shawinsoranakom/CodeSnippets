def check_batch_invariance(
        self, name, model, example_inputs, optimize_ctx, experiment, tag
    ):
        """
        Batch invariance check: run the compiled forward at N, N/2, ..., 1 and
        verify each output matches the reference sliced to that range bitwise.

        Always exercises forward-only, even under --training: batch invariance
        is a property of the forward pass; backward and optimizer step
        aggregate over the batch and are not batch-invariant by construction.
        Models with batch-dependent forward ops (e.g. BatchNorm in train mode)
        will still fail here -- that's inherent, not a harness bug.
        """
        start_stats = get_dynamo_stats()

        def record_status(status, dynamo_start_stats):
            self._write_accuracy_row(status, dynamo_start_stats, tag)
            return status

        if name in self.skip_accuracy_checks_large_models_dashboard:
            return record_status("pass_due_to_skip", dynamo_start_stats=start_stats)

        if (
            name in self.skip_accuracy_check_as_eager_non_deterministic
            or name in self.non_deterministic_models
        ):
            return record_status("pass_due_to_skip", dynamo_start_stats=start_stats)

        full_batch = current_batch_size
        if full_batch is None or full_batch < 2:
            return record_status("pass_due_to_skip", dynamo_start_stats=start_stats)

        # If no input tensor has batch as its first dim, the slicer below is a
        # no-op and the comparison would trivially pass without actually
        # exercising batch invariance. Skip rather than report a misleading pass.
        if not any(
            isinstance(x, torch.Tensor) and x.dim() > 0 and x.shape[0] == full_batch
            for x in pytree.tree_leaves(example_inputs)
        ):
            return record_status("pass_due_to_skip", dynamo_start_stats=start_stats)

        def make_slicer(target):
            def slicer(x):
                if x.dim() > 0 and x.shape[0] == full_batch:
                    return x[:target].contiguous()
                return x

            return slicer

        def run_fresh(inputs):
            # Rebuild model for every run so parameter-mutating side effects
            # (BN running stats, caches, etc.) from a prior run don't bleed
            # into the next comparison. Force eval mode regardless of
            # --training: dropout and train-mode BN are batch-size-dependent
            # by construction. Forward-only: backward/optimizer aggregate
            # over the batch and are not batch-invariant by construction.
            reset_rng_state()
            torch._dynamo.reset()
            torch._dynamo.utils.counters.clear()
            model_copy = self.deepcopy_and_maybe_parallelize(model)
            model_copy.eval()
            try:
                optimized_iter_fn = optimize_ctx(self.forward_pass)
                return self.run_n_iterations(model_copy, inputs, optimized_iter_fn)
            finally:
                del model_copy
                empty_gpu_cache(current_device)

        with self.pick_grad(name, self.args.training):
            model, example_inputs = self.maybe_cast(model, example_inputs)

            try:
                reference = run_fresh(clone_inputs(example_inputs))
            except Exception as e:
                log.exception("")
                status = (
                    "OOM"
                    if isinstance(e, torch.cuda.OutOfMemoryError)
                    else "fail_to_run"
                )
                return record_status(status, dynamo_start_stats=start_stats)

            size = full_batch // 2
            while size >= 1:
                slicer = make_slicer(size)
                sliced_inputs = tree_map_only(
                    torch.Tensor, slicer, clone_inputs(example_inputs)
                )

                try:
                    out = run_fresh(sliced_inputs)
                except Exception as e:
                    log.exception("")
                    status = (
                        "OOM"
                        if isinstance(e, torch.cuda.OutOfMemoryError)
                        else f"fail_to_run_at_batch_{size}"
                    )
                    return record_status(status, dynamo_start_stats=start_stats)

                reference_sliced = tree_map_only(torch.Tensor, slicer, reference)

                # Only compare batch-first output tensors. Aggregated outputs
                # (e.g. HuggingFace's MaskedLMOutput.loss) don't have a batch
                # dim and legitimately differ between batch sizes; comparing
                # them would produce misleading failures.
                def keep_batch_first(x):
                    return x if x.dim() > 0 and x.shape[0] == size else None

                ref_for_cmp = tree_map_only(
                    torch.Tensor, keep_batch_first, reference_sliced
                )
                out_for_cmp = tree_map_only(torch.Tensor, keep_batch_first, out)

                try:
                    is_same = bitwise_same(
                        ref_for_cmp, out_for_cmp, equal_nan=self.equal_nan
                    )
                except Exception:
                    is_same = False

                if not is_same:
                    if self.args.skip_accuracy_check:
                        return record_status(
                            "pass_due_to_skip", dynamo_start_stats=start_stats
                        )
                    return record_status(
                        f"fail_batch_invariance_at_{size}",
                        dynamo_start_stats=start_stats,
                    )

                size //= 2

        return record_status("pass", dynamo_start_stats=start_stats)