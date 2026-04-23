def test_state_dict_with_ignored_modules(
        self, state_dict_type, prefix, ignore_inner, mixed_precision
    ):
        # Initialize an FSDP-wrapped model with an ignored module that includes
        # both parameters and a buffer
        model = Model(
            wrap_fsdp=True,
            register_buffers=True,
            ignore_inner=ignore_inner,
            mixed_precision=mixed_precision,
        ).to(device_type)
        ignored_modules = [model.outer]
        ignored_tensor_to_tensor_name = {
            model.outer.bias: "outer.bias",
            model.outer.weight: "outer.weight",
        }
        if ignore_inner:
            ignored_tensor_to_tensor_name = {
                **ignored_tensor_to_tensor_name,
                model.inner.bias: "inner.bias",
                model.inner.weight: "inner.weight",
            }
        # Note that when model.inner is not ignored this test also ensures
        # non-ignored buffers are not cloned.
        buffer_to_buffer_name = {
            model.inner.buffer: "inner.buffer",
            model.outer.buffer: "outer.buffer",
        }
        # expect fp16 model.inner.buffer with mixed_precisions
        # expect fp32 sd.inner.buffer after restoring to original precision
        # so skip AssertEqual
        if mixed_precision and not ignore_inner:
            buffer_to_buffer_name.pop(model.inner.buffer)

        fsdp_model = FSDP(
            model,
            ignored_modules=ignored_modules,
            mixed_precision=MixedPrecision(
                param_dtype=torch.float16,
                reduce_dtype=torch.float16,
                buffer_dtype=torch.float16,
            )
            if mixed_precision
            else None,
        )
        prefix_str = "foo." if prefix else ""
        with FSDP.state_dict_type(fsdp_model, STATE_DICT_MAPPING[state_dict_type]):
            sd1 = _gather_state_dict(fsdp_model.state_dict(prefix=prefix_str))
        with FSDP.summon_full_params(fsdp_model):
            fsdp_params = deepcopy(list(fsdp_model.parameters()))
        # Check that the ignored parameters and all buffers are not cloned
        for tensor, tensor_name in {
            **ignored_tensor_to_tensor_name,
            **buffer_to_buffer_name,
        }.items():
            prefixed_tensor_name = f"{prefix_str}{tensor_name}"
            self.assertTrue(prefixed_tensor_name in sd1)
            self.assertEqual(
                tensor.data_ptr(),
                sd1[prefixed_tensor_name].data_ptr(),
                f"{prefixed_tensor_name}",
            )
        # should not apply mixed_precision to ignored buffers
        for buffer_name in buffer_to_buffer_name.values():
            prefixed_buffer_name = f"{prefix_str}{buffer_name}"
            self.assertTrue(prefixed_buffer_name in sd1)
            self.assertEqual(sd1[prefixed_buffer_name].dtype, torch.float32)
        # Check that the state dict can be loaded into a non-wrapped version of
        # the model
        nonwrapped_model = Model(wrap_fsdp=False, register_buffers=True).to(device_type)
        for param in nonwrapped_model.parameters():
            with torch.no_grad():
                param.zero_()

        to_load = {k[len(prefix_str) :]: v for k, v in sd1.items()}
        nonwrapped_model.load_state_dict(to_load, strict=True)
        local_params = list(nonwrapped_model.parameters())
        for fsdp_param, local_param in zip(fsdp_params, local_params):
            self.assertEqual(fsdp_param, local_param)
        # Check that if we save a state dict again, the ignored parameters and
        # buffer still have the same data pointer
        with FSDP.state_dict_type(fsdp_model, STATE_DICT_MAPPING[state_dict_type]):
            sd2 = fsdp_model.state_dict(prefix=prefix_str)
        for tensor, tensor_name in {
            **ignored_tensor_to_tensor_name,
            **buffer_to_buffer_name,
        }.items():
            prefixed_tensor_name = f"{prefix_str}{tensor_name}"
            self.assertTrue(prefixed_tensor_name in sd2)
            self.assertEqual(tensor.data_ptr(), sd2[prefixed_tensor_name].data_ptr())
            self.assertEqual(
                sd1[prefixed_tensor_name].data_ptr(),
                sd2[prefixed_tensor_name].data_ptr(),
            )