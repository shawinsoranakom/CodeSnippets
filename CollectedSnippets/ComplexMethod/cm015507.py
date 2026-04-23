def test_basic_checkpoint_end_to_end(
        self,
        cpu_offload: CPUOffload,
        offload_activations: bool,
        use_orig_params: bool,
    ):
        fsdp_kwargs = {"cpu_offload": cpu_offload, "use_orig_params": use_orig_params}
        global _save_on_cpu_called
        with patch_save_on_cpu(get_patched_save_on_cpu()):
            seq = TestFSDPCheckpoint.SequentialModule().to(device_type.type)
            # Runs FSDP with no checkpointing
            fsdp_only_seq = FSDP(deepcopy(seq), **fsdp_kwargs)
            # Runs checkpoint-wrapped FSDP
            if offload_activations:
                wrapper_to_use = offload_wrapper
            else:
                wrapper_to_use = checkpoint_wrapper
            checkpointed_fsdp = wrapper_to_use(
                FSDP(deepcopy(seq), **fsdp_kwargs),
            )
            # Runs FSDP-wrapped checkpointed module
            fsdp_wrapped_checkpoint = FSDP(
                wrapper_to_use(deepcopy(seq)),
                **fsdp_kwargs,
            )
            # Runs FSDP with manual calls to checkpoint.
            fsdp_call_checkpoint = FSDP(deepcopy(seq), **fsdp_kwargs)
            # note that reentrant-based checkpointing requires inputs to have grad
            # flag set.
            inp = torch.randn(10, 3, device=device_type.type, requires_grad=True)
            models = [
                fsdp_only_seq,
                checkpointed_fsdp,
                fsdp_wrapped_checkpoint,
                fsdp_call_checkpoint,
            ]
            # Ensure _save_on_cpu is not yet called
            self.assertFalse(_save_on_cpu_called)
            for i in range(6):
                losses = []
                outputs = []
                for m in models:
                    check_offload = (
                        m != fsdp_only_seq and i == 0 and offload_activations
                    )
                    if m == fsdp_call_checkpoint:
                        # _save_on_cpu should not be called yet
                        self.assertFalse(_save_on_cpu_called)
                        offload_ctx = (
                            get_patched_save_on_cpu()(pin_memory=True)
                            if offload_activations
                            else contextlib.nullcontext()
                        )
                        with offload_ctx:
                            out = checkpoint(m, inp, use_reentrant=True)
                    else:
                        # _save_on_cpu should not be called yet
                        self.assertFalse(_save_on_cpu_called)
                        out = m(inp)
                    if check_offload:
                        self.assertTrue(_save_on_cpu_called)
                    loss = out.sum()
                    loss.backward()
                    losses.append(loss)
                    outputs.append(out)
                    _save_on_cpu_called = False
                self._verify_parity(losses, outputs, models)
        dist.barrier()