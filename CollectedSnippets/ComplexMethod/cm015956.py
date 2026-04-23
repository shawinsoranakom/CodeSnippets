def test_new_spectral_norm(self):
        with set_default_dtype(torch.double):
            input = torch.randn(3, 5)
            m = nn.Linear(5, 7)
            m = torch.nn.utils.parametrizations.spectral_norm(m)
            spectral_norm_m = m.parametrizations.weight[0]

            self.assertEqual(spectral_norm_m._u.size(), torch.Size([m.weight.size(0)]))

            # .parametrizations.weight.original should be trainable
            self.assertTrue(hasattr(m.parametrizations.weight, "original"))
            self.assertTrue("original" in m.parametrizations.weight._parameters)

            # u should be just a reused buffer
            self.assertTrue(hasattr(spectral_norm_m, "_u"))
            self.assertTrue("_u" in spectral_norm_m._buffers)
            self.assertTrue("_v" in spectral_norm_m._buffers)

            # weight should be a plain attribute, not counted as a buffer or a param
            self.assertIsNotNone(m.weight)
            self.assertFalse("weight" in m._buffers)
            self.assertFalse("weight" in m._parameters)

            # it should also be sharing storage as `weight_orig`
            # self.assertEqual(m.parametrizations.weight.original.storage(), m.weight.storage())
            self.assertEqual(m.parametrizations.weight.original.size(), m.weight.size())
            self.assertEqual(
                m.parametrizations.weight.original.stride(), m.weight.stride()
            )

            m = torch.nn.utils.parametrize.remove_parametrizations(m, "weight")

            # spectral_norm is the only parametrization
            self.assertFalse(hasattr(m, "parametrizations"))
            self.assertTrue("weight" in m._parameters)

            # We can register spectral_norm multiple times on the same parameter
            # and on multiple parameters in the same module
            m = torch.nn.utils.parametrizations.spectral_norm(m, "weight")
            m = torch.nn.utils.parametrizations.spectral_norm(m, "weight")
            m = torch.nn.utils.parametrizations.spectral_norm(m, "bias")

            # If we remove the parametrization on bias, weight is still parametrized
            # Removing a parametrization runs forward in eval mode if leave_parametrized=True
            m = torch.nn.utils.parametrize.remove_parametrizations(m, "bias")
            self.assertTrue("bias" in m._parameters)
            self.assertTrue(hasattr(m, "parametrizations"))
            self.assertFalse("weight" in m._parameters)

            m = torch.nn.utils.parametrize.remove_parametrizations(m, "weight")
            # Neither weight and bias are parametrized
            self.assertFalse(hasattr(m, "parametrizations"))
            self.assertTrue("weight" in m._parameters)
            self.assertFalse(torch.nn.utils.parametrize.is_parametrized(m))

            # test correctness in training/eval modes and cpu/multi-gpu settings
            for apply_dp in (True, False):
                if apply_dp:
                    if not TEST_MULTIGPU:
                        continue
                    device = torch.device("cuda:0")

                    def maybe_wrap(m):
                        return torch.nn.DataParallel(m, [0, 1])

                else:
                    device = torch.device("cpu")

                    def maybe_wrap(m):
                        return m

                for requires_grad in (True, False):

                    def get_modules():
                        m = nn.Linear(3, 4).to(device)
                        m.weight.requires_grad_(requires_grad)
                        m = torch.nn.utils.parametrizations.spectral_norm(m)
                        wrapped_m = maybe_wrap(m)
                        spectral_norm_m = m.parametrizations.weight[0]
                        return m, wrapped_m, spectral_norm_m

                    input = torch.randn(2, 3, device=device)

                    m, wrapped_m, spectral_norm_m = get_modules()

                    self.assertTrue(hasattr(spectral_norm_m, "_u"))
                    u0 = spectral_norm_m._u.clone()
                    v0 = spectral_norm_m._v.clone()

                    # TEST TRAINING BEHAVIOR

                    # We perform GD first to modify the initial matrix
                    opt = torch.optim.SGD(wrapped_m.parameters(), lr=0.1)

                    opt.zero_grad()
                    wrapped_m(input).sum().backward()
                    opt.step()

                    out = wrapped_m(input)
                    if requires_grad:
                        # run forward again and assert that u and v are updated
                        self.assertNotEqual(u0, spectral_norm_m._u)
                        self.assertNotEqual(v0, spectral_norm_m._v)

                    # assert that backprop reaches original weight
                    # can't use gradcheck because the function changes as we
                    # activate through it in training mode
                    if requires_grad:
                        torch.autograd.grad(
                            out.sum(), m.parametrizations.weight.original
                        )

                    # test backward works with multiple forwards
                    # it uses training mode so we need to reset `u` and `v` vectors
                    # to same value at beginning for finite difference test to pass
                    saved_u = spectral_norm_m._u.clone()
                    saved_v = spectral_norm_m._v.clone()

                    def fn(input):
                        spectral_norm_m._u.data.copy_(saved_u)
                        spectral_norm_m._v.data.copy_(saved_v)
                        out0 = wrapped_m(input)
                        out1 = wrapped_m(input)
                        return out0 + out1

                    # Make sure we can compute gradients wrt to all the parameters in the case
                    # of double forward
                    fn(input.clone().requires_grad_()).sum().backward()
                    gradcheck(
                        fn, (input.clone().requires_grad_(),), check_batched_grad=False
                    )

                    # test removing
                    # spectral norm module needs to be in eval mode if we'd like to
                    # avoid doing another power iteration
                    m, wrapped_m, _ = get_modules()
                    pre_remove_out = wrapped_m(input)
                    if get_swap_module_params_on_conversion():
                        # When using the swap_tensors path, this is needed so that the autograd
                        # graph is not alive anymore.
                        pre_remove_out_ref = pre_remove_out.detach()
                        del pre_remove_out
                    else:
                        pre_remove_out_ref = pre_remove_out
                    m.eval()
                    m = torch.nn.utils.parametrize.remove_parametrizations(m, "weight")
                    self.assertEqual(wrapped_m(input), pre_remove_out_ref)

                    torch.nn.utils.parametrizations.spectral_norm(m)
                    for _ in range(3):
                        pre_remove_out = wrapped_m(input)
                    if get_swap_module_params_on_conversion():
                        # When using the swap_tensors path, this is needed so that the autograd
                        # graph is not alive anymore.
                        pre_remove_out_ref = pre_remove_out.detach()
                        del pre_remove_out
                    else:
                        pre_remove_out_ref = pre_remove_out
                    m.eval()
                    m = torch.nn.utils.parametrize.remove_parametrizations(m, "weight")
                    self.assertEqual(wrapped_m(input), pre_remove_out_ref)

                    # TEST EVAL BEHAVIOR
                    m, wrapped_m, spectral_norm_m = get_modules()
                    wrapped_m(input)
                    last_train_out = wrapped_m(input)
                    last_train_u = spectral_norm_m._u.clone()
                    last_train_v = spectral_norm_m._v.clone()
                    wrapped_m.zero_grad()
                    wrapped_m.eval()

                    eval_out0 = wrapped_m(input)
                    # assert eval gives same result as last training iteration
                    self.assertEqual(eval_out0, last_train_out)
                    # assert doing more iteration in eval don't change things
                    self.assertEqual(eval_out0, wrapped_m(input))
                    self.assertEqual(last_train_u, spectral_norm_m._u)
                    self.assertEqual(last_train_v, spectral_norm_m._v)

                    # FIXME: the code below is flaky when executed with DataParallel
                    # see https://github.com/pytorch/pytorch/issues/13818
                    if apply_dp:
                        continue

                    # test backward works with multiple forwards in mixed training
                    # and eval modes
                    # it uses training mode so we need to reset `u` and `v` vectors
                    # to same value at beginning for finite difference test to pass
                    saved_u = spectral_norm_m._u.clone()
                    saved_v = spectral_norm_m._v.clone()

                    def fn(input):
                        spectral_norm_m._u.data.copy_(saved_u)
                        spectral_norm_m._v.data.copy_(saved_v)
                        wrapped_m.train()
                        out0 = wrapped_m(input)
                        wrapped_m.eval()
                        out1 = wrapped_m(input)
                        wrapped_m.train()
                        out2 = wrapped_m(input)
                        wrapped_m.eval()
                        out3 = wrapped_m(input)
                        return out0 + out1 + out2 + out3

                    gradcheck(fn, (input.clone().requires_grad_(),))

                    # assert that backprop reaches weight_orig in eval
                    if requires_grad:

                        def fn(weight):
                            return wrapped_m(input)

                        gradcheck(fn, (m.parametrizations.weight.original,))