def extract_tensors_with_grads(
            output_val,
            grad_val,
            # Don't delete me- see [Note: ref cycle]
            extract_tensors_with_grads,
        ):
            if isinstance(output_val, torch.Tensor):
                if not output_val.requires_grad and output_val.grad_fn is None:
                    return
                if not isinstance(grad_val, (torch.Tensor, type(None))):
                    raise AssertionError(
                        f"Expected Tensor or None gradient but got {type(grad_val)}"
                    )
                stage_output_tensors.append(output_val)
                output_grad_tensors.append(grad_val)
            elif isinstance(output_val, (tuple, list)):
                if grad_val is None:
                    return
                if not isinstance(grad_val, (tuple, list)):
                    raise AssertionError(
                        f"grad_value expected to have type {type(output_val)} but got {type(grad_val)}"
                    )
                if not len(output_val) == len(grad_val):
                    raise AssertionError(
                        f"Expected len(output_val) == len(grad_val), got {len(output_val)} != {len(grad_val)}"
                    )
                for ov, gv in zip(output_val, grad_val):
                    extract_tensors_with_grads(
                        ov,
                        gv,
                        extract_tensors_with_grads,
                    )
            elif isinstance(output_val, dict):
                if grad_val is None:
                    return
                if not isinstance(grad_val, dict):
                    raise AssertionError(f"Expected dict, got {type(grad_val)}")
                if not set(output_val.keys()) == set(grad_val.keys()):
                    raise AssertionError(
                        f"Expected keys {set(output_val.keys())}, got {set(grad_val.keys())}"
                    )
                for k in output_val:
                    extract_tensors_with_grads(
                        output_val[k], grad_val[k], extract_tensors_with_grads
                    )
            else:
                # Output is a non-tensor type; just ignore it
                pass