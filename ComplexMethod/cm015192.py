def test_function_returns_input(
        self, device, inner_requires_grad, save_for, save_tensors, mark_dirty
    ):
        class A(torch.autograd.Function):
            @staticmethod
            def forward(x):
                return x

            @staticmethod
            def setup_context(ctx, inputs, output):
                if save_for == "jvp":
                    save_fn = ctx.save_for_forward
                else:
                    save_fn = ctx.save_for_backward

                if mark_dirty:
                    ctx.mark_dirty(inputs[0])

                if save_tensors == "input":
                    save_fn(inputs[0])
                elif save_tensors == "output":
                    save_fn(output)
                elif save_tensors == "neither":
                    pass

            @staticmethod
            def backward(ctx, grad_output):
                return grad_output

            @staticmethod
            def jvp(ctx, x_t):
                # NB: the logic to check ctx.save_for_forward happens
                #     before we reach this!
                if mark_dirty:
                    ret = x_t.add_(0)
                else:
                    ret = x_t.view_as(x_t)
                return ret

        def fn(x):
            return A.apply(x.clone())

        err_msg = "A input that has been returned as-is"

        a = torch.tensor(2.0, device=device, requires_grad=inner_requires_grad)
        a_t = torch.tensor(2.0, device=device, requires_grad=inner_requires_grad)
        if save_tensors in ("input", "output") and not mark_dirty:
            with self.assertRaisesRegex(RuntimeError, err_msg):
                grad(fn)(a)
            with self.assertRaisesRegex(RuntimeError, err_msg):
                jvp(fn, (a,), (a_t,))
        else:
            grad(fn)(a)
            jvp(fn, (a,), (a_t,))

        a = torch.tensor(2.0, device=device, requires_grad=inner_requires_grad).clone()
        a_t = torch.tensor(
            2.0, device=device, requires_grad=inner_requires_grad
        ).clone()

        if save_tensors in ("input", "output") and not mark_dirty:
            with self.assertRaisesRegex(RuntimeError, err_msg):
                A.apply(a)
            with self.assertRaisesRegex(RuntimeError, err_msg):
                with fwAD.dual_level():
                    A.apply(fwAD.make_dual(a, a_t))
        else:
            b = A.apply(a)
            if mark_dirty:
                self.assertTrue(a is b)
            if not (
                mark_dirty and save_for == "vjp" and save_tensors in ("input", "output")
            ):
                # TODO(soulitzer): https://github.com/pytorch/pytorch/issues/97827
                with fwAD.dual_level():
                    a_dual = fwAD.make_dual(a, a_t)
                    b_dual = A.apply(a_dual)
                if mark_dirty:
                    self.assertTrue(a_dual is b_dual)