def test_spectral_norm(self):
        input = torch.randn(3, 5)
        m = nn.Linear(5, 7)
        m = torch.nn.utils.spectral_norm(m)

        self.assertEqual(m.weight_u.size(), torch.Size([m.weight.size(0)]))
        # weight_orig should be trainable
        self.assertTrue(hasattr(m, 'weight_orig'))
        self.assertTrue('weight_orig' in m._parameters)
        # weight_u should be just a reused buffer
        self.assertTrue(hasattr(m, 'weight_u'))
        self.assertTrue('weight_u' in m._buffers)
        self.assertTrue('weight_v' in m._buffers)
        # weight should be a plain attribute, not counted as a buffer or a param
        self.assertFalse('weight' in m._buffers)
        self.assertFalse('weight' in m._parameters)
        # it should also be sharing storage as `weight_orig`
        self.assertEqual(m.weight_orig.storage(), m.weight.storage())
        self.assertEqual(m.weight_orig.size(), m.weight.size())
        self.assertEqual(m.weight_orig.stride(), m.weight.stride())

        m = torch.nn.utils.remove_spectral_norm(m)
        self.assertFalse(hasattr(m, 'weight_orig'))
        self.assertFalse(hasattr(m, 'weight_u'))
        # weight should be converted back as a parameter
        self.assertTrue(hasattr(m, 'weight'))
        self.assertTrue('weight' in m._parameters)

        with self.assertRaisesRegex(RuntimeError, 'register two spectral_norm hooks'):
            m = torch.nn.utils.spectral_norm(m)
            m = torch.nn.utils.spectral_norm(m)

        # test correctness in training/eval modes and cpu/multi-gpu settings
        for apply_dp in (True, False):
            if apply_dp:
                if not TEST_MULTIGPU:
                    continue
                device = torch.device('cuda:0')

                def maybe_wrap(m):
                    return torch.nn.DataParallel(m, [0, 1])
            else:
                device = torch.device('cpu')

                def maybe_wrap(m):
                    return m

            for requires_grad in (True, False):
                m = nn.Linear(3, 4).to(device)
                m.weight.requires_grad_(requires_grad)
                m = torch.nn.utils.spectral_norm(m)
                wrapped_m = maybe_wrap(m)
                self.assertTrue(hasattr(m, 'weight_u'))
                u0 = m.weight_u.clone()
                v0 = m.weight_v.clone()

                # TEST TRAINING BEHAVIOR

                # assert that u and v are updated
                input = torch.randn(2, 3, device=device)
                out = wrapped_m(input)
                self.assertNotEqual(u0, m.weight_u)
                self.assertNotEqual(v0, m.weight_v)

                # assert that backprop reaches weight_orig
                # can't use gradcheck because the function changes as we
                # activate through it in training mode
                if requires_grad:
                    torch.autograd.grad(out.sum(), m.weight_orig)

                # test backward works with multiple forwards
                # it uses training mode so we need to reset `u` and `v` vectors
                # to same value at beginning for finite difference test to pass
                saved_u = m.weight_u.clone()
                saved_v = m.weight_v.clone()

                def fn(input):
                    m.weight_u.data.copy_(saved_u)
                    m.weight_v.data.copy_(saved_v)
                    out0 = wrapped_m(input)
                    out1 = wrapped_m(input)
                    return out0 + out1

                gradcheck(fn, (input.clone().requires_grad_(),), check_batched_grad=False)

                # test removing
                pre_remove_out = wrapped_m(input)
                m = torch.nn.utils.remove_spectral_norm(m)
                self.assertEqual(wrapped_m(input), pre_remove_out)

                m = torch.nn.utils.spectral_norm(m)
                for _ in range(3):
                    pre_remove_out = wrapped_m(input)
                m = torch.nn.utils.remove_spectral_norm(m)
                self.assertEqual(wrapped_m(input), pre_remove_out)

                # TEST EVAL BEHAVIOR

                m = torch.nn.utils.spectral_norm(m)
                wrapped_m(input)
                last_train_out = wrapped_m(input)
                last_train_u = m.weight_u.clone()
                last_train_v = m.weight_v.clone()
                wrapped_m.zero_grad()
                wrapped_m.eval()

                eval_out0 = wrapped_m(input)
                # assert eval gives same result as last training iteration
                self.assertEqual(eval_out0, last_train_out)
                # assert doing more iteration in eval don't change things
                self.assertEqual(eval_out0, wrapped_m(input))
                self.assertEqual(last_train_u, m.weight_u)
                self.assertEqual(last_train_v, m.weight_v)

                # FIXME: the code below is flaky when executed with DataParallel
                # see https://github.com/pytorch/pytorch/issues/13818
                if apply_dp:
                    continue

                # test backward works with multiple forwards in mixed training
                # and eval modes
                # it uses training mode so we need to reset `u` and `v` vectors
                # to same value at beginning for finite difference test to pass
                saved_u = m.weight_u.clone()
                saved_v = m.weight_v.clone()

                def fn(input):
                    m.weight_u.data.copy_(saved_u)
                    m.weight_v.data.copy_(saved_v)
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

                    gradcheck(fn, (m.weight_orig,))