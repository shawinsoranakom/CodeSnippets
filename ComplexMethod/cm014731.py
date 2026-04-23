def test_batchnorm_raises_error_if_running_var_or_running_mean_have_forward_grad(self):
        args = (
            torch.randn(3, 2, 5),  # input
            torch.randn(2),  # running_mean
            torch.randn(2),  # running_var
        )
        kwargs = {'training': False, 'momentum': -1.2}
        fn = partial(F.batch_norm, **kwargs)

        for dual_indices in ((0,), (1,), (1, 2), (0, 1), (0, 1, 2),):
            tangents = tuple(torch.rand_like(x) for x in args)

            with fwAD.dual_level():
                duals = [fwAD.make_dual(primal, tangent) if i in dual_indices else primal
                         for i, (primal, tangent) in enumerate(zip(args, tangents))]
                msg = "batch_norm is not differentiable wrt running_mean and running_var"
                # 0 needs to have forward grad because otherwise we won't even run batch_norm_jvp
                if (1 in dual_indices or 2 in dual_indices) and 0 in dual_indices:
                    with self.assertRaisesRegex(RuntimeError, msg):
                        fn(*duals)
                else:
                    fn(*duals)