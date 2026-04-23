def _test_cond_autograd(self, cond_fct, pred_fn, true_fn, false_fn, operands):
        from torch.fx.passes.shape_prop import _extract_tensor_metadata, TensorMetadata

        # This is a helper function that extracts the metadata from the tensor and
        # sets the requires_grad flag to false. This is needed as we compare the
        # metadata of the operands and the gradients
        def _extract_tensor_metadata_except_requires_grad(arg):
            metadata = _extract_tensor_metadata(arg)
            metadata = TensorMetadata(
                metadata.shape,
                metadata.dtype,
                False,
                metadata.stride,
                metadata.memory_format,
                metadata.is_quantized,
                metadata.qparams,
            )
            return metadata

        # Comparison of FWD path
        cond_outputs = cond_fct(pred_fn(*operands), true_fn, false_fn, operands)
        operands_forced_grad = [o.clone().detach() for o in operands]
        for o in operands_forced_grad:
            o.requires_grad = True
        cond_outputs_exp = (
            true_fn(*operands_forced_grad)
            if pred_fn(*operands_forced_grad)
            else false_fn(*operands_forced_grad)
        )
        self.assertEqual(cond_outputs, cond_outputs_exp)

        # Comparison of BWD path
        cond_inputs = [o for o in operands if o.requires_grad]
        cond_inputs_exp = [o for o in operands_forced_grad if o.requires_grad]

        # Check if at least some operators require grads
        if len(cond_inputs) > 0:
            grad_inputs = torch.autograd.grad(
                cond_outputs, cond_inputs, allow_unused=True, retain_graph=True
            )
            grad_inputs_exp = torch.autograd.grad(
                cond_outputs_exp,
                cond_inputs_exp,
                allow_unused=True,
                materialize_grads=True,
            )

            grad_exp_masked = [
                g for g, o in zip(grad_inputs_exp, operands) if o.requires_grad
            ]
            self.assertEqual(grad_exp_masked, grad_inputs)

            # Extraction and comparison of Metadata of operands and gradients
            operands_metadata = [
                _extract_tensor_metadata_except_requires_grad(o) for o in cond_inputs
            ]
            grad_metadata = [
                _extract_tensor_metadata_except_requires_grad(o) for o in grad_inputs
            ]
            self.assertTrue(
                all(op == g for op, g in zip(operands_metadata, grad_metadata))
            )

        return cond_outputs, cond_inputs