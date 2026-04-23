def test_checkpoint_fsdp_wrapping(
        self,
        cpu_offload: CPUOffload,
        offload_activations: bool,
        use_orig_params: bool,
    ):
        # Test checkpoint(FSDP(layer1), FSDP(layer2), ....)
        if offload_activations:
            wrapper_to_use = offload_wrapper
        else:
            wrapper_to_use = checkpoint_wrapper
        fsdp_kwargs = {"cpu_offload": cpu_offload, "use_orig_params": use_orig_params}
        ckpt_sequential_wrapped_fsdp = wrapper_to_use(
            TestFSDPCheckpoint.SequentialModule(
                wrap_fsdp=True,
                **fsdp_kwargs,
            ),
        )
        # Test FSDP(checkpoint(layer1)), FSDP(checkpoint(layer2)), ....
        inner_ckpt = TestFSDPCheckpoint.SequentialModule(
            checkpoint_layer=True,
            offload_activations=offload_activations,
            wrap_fsdp=True,
            **fsdp_kwargs,
        )
        baseline = TestFSDPCheckpoint.SequentialModule(
            wrap_fsdp=True,
            **fsdp_kwargs,
        )
        # note that reentrant-based checkpointing requires inputs to have grad
        # flag set.
        inp = torch.randn(10, 3, device=device_type.type, requires_grad=True)
        global _save_on_cpu_called
        models = [ckpt_sequential_wrapped_fsdp, inner_ckpt, baseline]
        with patch_save_on_cpu(get_patched_save_on_cpu()):
            for i in range(2):
                losses = []
                outputs = []
                for m in models:
                    check_offload = m != baseline and i == 0 and offload_activations
                    if check_offload:
                        self.assertFalse(_save_on_cpu_called)
                    out = m(inp)
                    if check_offload:
                        self.assertTrue(_save_on_cpu_called)
                        _save_on_cpu_called = False
                    loss = out.sum()
                    loss.backward()
                    losses.append(loss)
                    outputs.append(out)
                self._verify_parity(losses, outputs, models)
        dist.barrier()