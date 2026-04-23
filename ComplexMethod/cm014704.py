def test_complex(self, device, dtype, optim_info):
        optim_cls = optim_info.optim_cls
        # Skip differentiable testing for now, see https://github.com/pytorch/pytorch/issues/116490
        # Also skip fused, since our fused kernels do not support complex
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable", "fused")
        )
        for optim_input in all_optim_inputs:
            # Last param is intentionally real to test that we can mix real and complex
            complex_params = [
                torch.randn(10, 5, device=device, dtype=dtype, requires_grad=True),
                torch.randn(10, device=device, dtype=dtype, requires_grad=True),
                torch.randn(
                    10, 5, device=device, dtype=torch.float32, requires_grad=True
                ),
            ]
            real_params = [
                (
                    torch.view_as_real(param).detach().clone().requires_grad_()
                    if param.is_complex()
                    else param.detach().clone().requires_grad_()
                )
                for param in complex_params
            ]

            complex_optimizer = optim_cls(complex_params, **optim_input.kwargs)
            real_optimizer = optim_cls(real_params, **optim_input.kwargs)
            real_steps = []
            complex_steps = []
            grads_losses = []

            def real_closure():
                for param in real_params:
                    grad = torch.randn_like(param)
                    param.grad = grad
                    real_steps.append(param.detach().clone())
                    grads_losses.append(grad.clone())
                loss = torch.randn(1)
                grads_losses.append(loss.clone())
                return loss

            def complex_closure():
                for param in complex_params:
                    if torch.is_complex(param):
                        grad = torch.view_as_complex(grads_losses.pop(0))
                        complex_steps.append(torch.view_as_real_copy(param.detach()))
                    else:
                        grad = grads_losses.pop(0)
                        complex_steps.append(param.detach().clone())
                    param.grad = grad
                return grads_losses.pop(0)

            for _ in range(3):
                if optim_info.step_requires_closure:
                    # LBFGS, for example, requires closure and calls it internally
                    real_optimizer.step(real_closure)
                    complex_optimizer.step(complex_closure)
                else:
                    # For other optimizers, we call closure explicitly to set the gradients
                    real_closure()
                    complex_closure()
                    real_optimizer.step()
                    complex_optimizer.step()

            # Final Parameters should be the same
            complex_params_asreal = [
                torch.view_as_real(param) if param.is_complex() else param
                for param in complex_params
            ]
            self.assertEqual(real_params, complex_params_asreal)

            # All intermediate steps should also be the same
            # also checks steps taken within for example a line search
            self.assertEqual(complex_steps, real_steps)