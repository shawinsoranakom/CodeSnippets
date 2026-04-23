def check_accuracy(
        self, name, model, example_inputs, optimize_ctx, experiment, tag
    ):
        """
        Checks accuracy.
        1) Collect the outputs with fp64 datatype. This is useful for error checking.
        2) Checks if eager itself has variations.
        """
        start_stats = get_dynamo_stats()

        def record_status(accuracy_status, dynamo_start_stats):
            """
            Records the status in the csv file
            """
            if current_name in self.non_deterministic_models:
                if accuracy_status in (
                    "pass",
                    "eager_two_runs_differ",
                    "fail_accuracy",
                ):
                    accuracy_status = "pass"

            self._write_accuracy_row(accuracy_status, dynamo_start_stats, tag)
            return accuracy_status

        if name in self.skip_accuracy_checks_large_models_dashboard:
            return record_status("pass_due_to_skip", dynamo_start_stats=start_stats)

        # Skip all accuracy check for the torchao backend
        if self.args.backend == "torchao":
            return record_status("pass_due_to_skip", dynamo_start_stats=start_stats)

        with self.pick_grad(name, self.args.training):
            # Collect the fp64 reference outputs to be used later for accuracy checking.
            fp64_outputs = None
            model_fp64 = None
            inputs_fp64 = None
            try:
                model_fp64, inputs_fp64 = cast_to_fp64(
                    self.deepcopy_and_maybe_parallelize(model),
                    clone_inputs(example_inputs),
                )
                self.init_optimizer(name, current_device, model_fp64.parameters())
                fp64_outputs = self.run_n_iterations(
                    model_fp64, inputs_fp64, self.model_iter_fn
                )
                fp64_outputs = tree_map(
                    lambda x: x.to(torch.float64)
                    if isinstance(x, torch.Tensor) and x.is_floating_point()
                    else x,
                    fp64_outputs,
                )
            except Exception:
                log.warning(
                    "fp64 golden ref were not generated for %s. Setting accuracy check to cosine",
                    name,
                    exc_info=True,
                )
                self.args.cosine = True
                fp64_outputs = None
            finally:
                del model_fp64, inputs_fp64
                empty_gpu_cache(current_device)

            tolerance, cos_similarity = self.get_tolerance_and_cosine_flag(
                self.args.training, current_device, name
            )

            # Cast the model to float16/float32 as necessary
            model, example_inputs = self.maybe_cast(model, example_inputs)
            accuracy_status = "pass"

            # Get results of native pytorch
            reset_rng_state()
            model_copy = None
            try:
                with torch.compiler.set_stance("force_eager"):
                    model_copy = self.deepcopy_and_maybe_parallelize(model)
                    self.init_optimizer(name, current_device, model_copy.parameters())
                    correct_result = self.run_n_iterations(
                        model_copy, clone_inputs(example_inputs), self.model_iter_fn
                    )
            except Exception as e:
                accuracy_status = (
                    "eager_1st_run_OOM"
                    if isinstance(e, torch.cuda.OutOfMemoryError)
                    else "eager_1st_run_fail"
                )
                log.exception("")
                return record_status(accuracy_status, dynamo_start_stats=start_stats)
            finally:
                del model_copy
                empty_gpu_cache(current_device)

            # Rerun native pytorch
            reset_rng_state()
            model_copy = None
            try:
                with torch.compiler.set_stance("force_eager"):
                    model_copy = self.deepcopy_and_maybe_parallelize(model)
                    self.init_optimizer(name, current_device, model_copy.parameters())
                    correct_rerun_result = self.run_n_iterations(
                        model_copy, clone_inputs(example_inputs), self.model_iter_fn
                    )
            except Exception as e:
                accuracy_status = (
                    "eager_2nd_run_OOM"
                    if isinstance(e, torch.cuda.OutOfMemoryError)
                    else "eager_2nd_run_fail"
                )
                log.exception("")
                return record_status(accuracy_status, dynamo_start_stats=start_stats)
            finally:
                del model_copy
                empty_gpu_cache(current_device)

            # Two eager runs should have exactly same result, within tolerance.
            # TODO If we want the above to be true, then deterministic should be set.
            # For example, MIOpen convolutions could be implemented with non-deterministic algos.
            is_same = True
            try:
                if (
                    name not in self.skip_accuracy_check_as_eager_non_deterministic
                    and not same(
                        correct_result,
                        correct_rerun_result,
                        fp64_ref=None,
                        cos_similarity=False,
                        tol=tolerance if torch.version.hip else 0,
                        equal_nan=self.equal_nan,
                        use_larger_multiplier_for_smaller_tensor=self.use_larger_multiplier_for_smaller_tensor(
                            name
                        ),
                    )
                ):
                    is_same = False
            except Exception:
                # Sometimes torch.allclose may throw RuntimeError
                is_same = False

            if not is_same:
                accuracy_status = "eager_two_runs_differ"
                return record_status(accuracy_status, dynamo_start_stats=start_stats)

            correct_rerun_result = None

            # Support multiple accuracy check runs for flaky models
            accuracy_check_runs = self.get_accuracy_check_runs(name)
            pass_count = 0

            for run_idx in range(accuracy_check_runs):
                # Run with Dynamo
                reset_rng_state()
                torch._dynamo.reset()
                torch._dynamo.utils.counters.clear()
                model_copy = None
                run_passed = True

                try:
                    model_copy = self.deepcopy_and_maybe_parallelize(model)
                    self.init_optimizer(name, current_device, model_copy.parameters())
                    if (
                        self.args.export
                        or self.args.export_aot_inductor
                        or self.args.export_nativert
                        or self.args.torchscript_jit_trace
                        or self.args.aot_precompile
                    ):
                        # apply export on module directly
                        # no need for n iterations
                        # the logic should be the same to self.model_iter_fn (forward_pass)
                        with self.autocast(**self.autocast_arg):
                            optimized_model_iter_fn = optimize_ctx(
                                model_copy, example_inputs
                            )
                            new_result = optimized_model_iter_fn(
                                model_copy, example_inputs
                            )
                    else:
                        optimized_model_iter_fn = optimize_ctx(self.model_iter_fn)
                        new_result = self.run_n_iterations(
                            model_copy, example_inputs, optimized_model_iter_fn
                        )
                except Exception as e:
                    log.exception("")
                    print(
                        "TorchDynamo optimized model failed to run because of following error"
                    )
                    accuracy_status = (
                        "OOM"
                        if isinstance(e, torch.cuda.OutOfMemoryError)
                        else "fail_to_run"
                    )
                    return record_status(
                        accuracy_status, dynamo_start_stats=start_stats
                    )
                finally:
                    del model_copy

                if name in self.skip_accuracy_check_as_eager_non_deterministic:
                    return record_status(
                        "pass_due_to_skip", dynamo_start_stats=start_stats
                    )

                force_max_multiplier = False
                if (
                    self.args.freezing
                    and self.args.bfloat16
                    and torch._dynamo.utils.counters["inductor"]["binary_folding_conv"]
                    > 0
                ):
                    force_max_multiplier = True

                try:
                    if self.args.training and self.args.amp:
                        if process_fn := self.get_output_amp_train_process_func.get(
                            name, None
                        ):
                            correct_result = process_fn(correct_result)
                            new_result = process_fn(new_result)
                            fp64_outputs = process_fn(fp64_outputs)

                    if (
                        self.args.save_model_outputs_to
                        and self.args.compare_model_outputs_with
                        and self.args.save_model_outputs_to
                        == self.args.compare_model_outputs_with
                    ):
                        log.warning(
                            "args.save_model_outputs_to and args.compare_model_outputs_with points to the same path."
                            "Result will be undefined."
                        )

                    if self.args.save_model_outputs_to:
                        print(
                            f"Save model outputs to: {self.args.save_model_outputs_to}"
                        )
                        torch.save(new_result, self.args.save_model_outputs_to)

                    if self.args.compare_model_outputs_with:
                        print(
                            f"Load model outputs from {self.args.compare_model_outputs_with} to compare"
                        )
                        saved_result = torch.load(
                            self.args.compare_model_outputs_with, weights_only=False
                        )
                        is_bitwise_same = bitwise_same(saved_result, new_result)
                        if not is_bitwise_same:
                            print(
                                "The result is not bitwise equivalent to the previously saved result"
                            )
                            return record_status(
                                "not_bitwise_equivalent",
                                dynamo_start_stats=start_stats,
                            )

                        print(
                            "The result is bitwise equivalent to the previously saved result"
                        )
                        del saved_result

                    if not same(
                        correct_result,
                        new_result,
                        fp64_outputs,
                        equal_nan=self.equal_nan,
                        use_larger_multiplier_for_smaller_tensor=self.use_larger_multiplier_for_smaller_tensor(
                            name
                        ),
                        cos_similarity=cos_similarity,
                        tol=tolerance,
                        force_max_multiplier=force_max_multiplier,
                        use_iou_for_bool=self.use_iou_for_bool_accuracy(name),
                        iou_threshold=self.get_iou_threshold(name),
                    ):
                        run_passed = False
                except Exception:
                    # Sometimes torch.allclose may throw RuntimeError
                    run_passed = False

                if run_passed:
                    pass_count += 1

                if accuracy_check_runs > 1:
                    log.info(
                        "Accuracy check run %d/%d: %s",
                        run_idx + 1,
                        accuracy_check_runs,
                        "passed" if run_passed else "failed",
                    )

            # Pass if majority of runs pass (more than half)
            is_same = pass_count > accuracy_check_runs // 2

            if accuracy_check_runs > 1:
                log.info(
                    "Accuracy check summary: %d/%d runs passed, %s",
                    pass_count,
                    accuracy_check_runs,
                    "PASS" if is_same else "FAIL",
                )

            if not is_same:
                if self.args.skip_accuracy_check:
                    accuracy_status = "pass_due_to_skip"
                else:
                    accuracy_status = "fail_accuracy"
                return record_status(accuracy_status, dynamo_start_stats=start_stats)

        return record_status(accuracy_status, dynamo_start_stats=start_stats)