def test_scalar_check(self, device):
        zero_d = torch.randn((), device=device)
        one_d = torch.randn((1,), device=device)

        # remainder
        self.assertEqual((), torch.remainder(zero_d, zero_d).shape)
        self.assertEqual((), torch.remainder(zero_d, 2).shape)
        self.assertEqual((1,), torch.remainder(zero_d, one_d).shape)
        self.assertEqual((1,), torch.remainder(one_d, zero_d).shape)

        # fmod
        self.assertEqual((), torch.fmod(zero_d, zero_d).shape)
        self.assertEqual((), torch.fmod(zero_d, 2).shape)
        self.assertEqual((1,), torch.fmod(zero_d, one_d).shape)
        self.assertEqual((1,), torch.fmod(one_d, zero_d).shape)

        # exp, cos, cosh, tan, atan, tanh, erf, erfc, reciprocal
        self.assertEqual((), torch.exp(zero_d).shape)
        self.assertEqual((), torch.cos(zero_d).shape)
        self.assertEqual((), torch.cosh(zero_d).shape)
        self.assertEqual((), torch.tan(zero_d).shape)
        self.assertEqual((), torch.atan(zero_d).shape)
        self.assertEqual((), torch.acosh(zero_d).shape)
        self.assertEqual((), torch.asinh(zero_d).shape)
        self.assertEqual((), torch.atanh(zero_d).shape)
        self.assertEqual((), torch.tanh(zero_d).shape)
        self.assertEqual((), torch.erf(zero_d).shape)
        self.assertEqual((), torch.erfc(zero_d).shape)
        self.assertEqual((), torch.reciprocal(zero_d).shape)
        self.assertEqual((1,), torch.exp(one_d).shape)
        self.assertEqual((1,), torch.cos(one_d).shape)
        self.assertEqual((1,), torch.cosh(one_d).shape)
        self.assertEqual((1,), torch.tan(one_d).shape)
        self.assertEqual((1,), torch.atan(one_d).shape)
        self.assertEqual((1,), torch.acosh(one_d).shape)
        self.assertEqual((1,), torch.asinh(one_d).shape)
        self.assertEqual((1,), torch.atanh(one_d).shape)
        self.assertEqual((1,), torch.tanh(one_d).shape)
        self.assertEqual((1,), torch.erf(one_d).shape)
        self.assertEqual((1,), torch.erfc(one_d).shape)
        self.assertEqual((1,), torch.reciprocal(one_d).shape)

        # clamp
        self.assertEqual((), torch.clamp(zero_d, min=0, max=1).shape)
        self.assertEqual((), torch.clamp(zero_d, min=0).shape)
        self.assertEqual((), torch.clamp(zero_d, max=1).shape)
        self.assertEqual((1,), torch.clamp(one_d, min=0, max=1).shape)
        self.assertEqual((1,), torch.clamp(one_d, min=0).shape)
        self.assertEqual((1,), torch.clamp(one_d, max=1).shape)

        # cumsum, cumprod, cummax, cummin
        self.assertEqual((), torch.logcumsumexp(zero_d, 0).shape)
        self.assertEqual((), torch.cumsum(zero_d, 0).shape)
        self.assertEqual((), torch.cumprod(zero_d, 0).shape)
        self.assertEqual((), torch.cummax(zero_d, 0)[0].shape)
        self.assertEqual((), torch.cummin(zero_d, 0)[0].shape)

        # sort, topk
        self.assertEqual([(), ()], [x.shape for x in torch.sort(zero_d, 0, False)])
        self.assertEqual([(), ()], [x.shape for x in torch.sort(zero_d, 0, True)])
        self.assertEqual([(), ()], [x.shape for x in torch.topk(zero_d, 1, 0, False)])
        self.assertEqual([(), ()], [x.shape for x in torch.topk(zero_d, 1, 0, True)])

        # max, min
        self.assertEqual((), torch.max(zero_d, zero_d).shape)
        self.assertEqual((1,), torch.max(one_d, zero_d).shape)
        self.assertEqual((1,), torch.max(zero_d, one_d).shape)
        self.assertEqual((), torch.min(zero_d, zero_d).shape)
        self.assertEqual((1,), torch.min(one_d, zero_d).shape)
        self.assertEqual((1,), torch.min(zero_d, one_d).shape)

        zero_d_int = torch.tensor(1, device=device)
        one_d_int = torch.tensor([1], device=device)

        # lshift, rshift
        self.assertEqual((), (zero_d_int >> zero_d_int).shape)
        self.assertEqual((), (zero_d_int >> 1).shape)
        self.assertEqual((1,), (one_d_int >> zero_d_int).shape)
        self.assertEqual((1,), (zero_d_int >> one_d_int).shape)
        self.assertEqual((1,), (one_d_int >> 1).shape)

        self.assertEqual((), (zero_d_int << zero_d_int).shape)
        self.assertEqual((), (zero_d_int << 1).shape)
        self.assertEqual((1,), (one_d_int << zero_d_int).shape)
        self.assertEqual((1,), (zero_d_int << one_d_int).shape)
        self.assertEqual((1,), (one_d_int << 1).shape)

        # or
        self.assertEqual((), (zero_d_int | zero_d_int).shape)
        self.assertEqual((), (zero_d_int | 1).shape)
        self.assertEqual((1,), (one_d_int | zero_d_int).shape)
        self.assertEqual((1,), (zero_d_int | one_d_int).shape)
        self.assertEqual((1,), (one_d_int | 1).shape)

        # and
        self.assertEqual((), (zero_d_int & zero_d_int).shape)
        self.assertEqual((), (zero_d_int & 1).shape)
        self.assertEqual((1,), (one_d_int & zero_d_int).shape)
        self.assertEqual((1,), (zero_d_int & one_d_int).shape)
        self.assertEqual((1,), (one_d_int & 1).shape)

        # clone
        self.assertEqual((), zero_d.clone().shape)

        zero_d_bool = torch.tensor(True, device=device)
        one_d_bool = torch.tensor([True], device=device)

        # masked_select
        self.assertEqual((1,), torch.masked_select(zero_d_bool, zero_d_bool).shape)
        self.assertEqual((1,), torch.masked_select(zero_d_bool, one_d_bool).shape)
        self.assertEqual((1,), torch.masked_select(one_d_bool, zero_d_bool).shape)

        torch.tensor(1, dtype=torch.uint8, device=device)
        torch.tensor([1], dtype=torch.uint8, device=device)

        # mode
        self.assertEqual([(), ()], [x.shape for x in torch.mode(zero_d, dim=0, keepdim=True)])
        self.assertEqual([(), ()], [x.shape for x in torch.mode(zero_d, dim=0, keepdim=False)])
        self.assertEqual([(1,), (1,)], [x.shape for x in torch.mode(one_d, dim=0, keepdim=True)])
        self.assertEqual([(), ()], [x.shape for x in torch.mode(one_d, dim=0, keepdim=False)])

        # max
        self.assertEqual([(), ()], [x.shape for x in torch.max(zero_d, dim=0, keepdim=True)])
        self.assertEqual([(), ()], [x.shape for x in torch.max(zero_d, dim=0, keepdim=False)])
        self.assertEqual([(1,), (1,)], [x.shape for x in torch.max(one_d, dim=0, keepdim=True)])
        self.assertEqual([(), ()], [x.shape for x in torch.max(one_d, dim=0, keepdim=False)])

        # amax
        self.assertEqual((), torch.amax(zero_d, dim=0, keepdim=True).shape)
        self.assertEqual((), torch.amax(zero_d, dim=0, keepdim=False).shape)
        self.assertEqual((1,), torch.amax(one_d, dim=0, keepdim=True).shape)
        self.assertEqual((), torch.amax(one_d, dim=0, keepdim=False).shape)

        # min
        self.assertEqual([(), ()], [x.shape for x in torch.min(zero_d, dim=0, keepdim=True)])
        self.assertEqual([(), ()], [x.shape for x in torch.min(zero_d, dim=0, keepdim=False)])
        self.assertEqual([(1,), (1,)], [x.shape for x in torch.min(one_d, dim=0, keepdim=True)])
        self.assertEqual([(), ()], [x.shape for x in torch.min(one_d, dim=0, keepdim=False)])

        # amin
        self.assertEqual((), torch.amin(zero_d, dim=0, keepdim=True).shape)
        self.assertEqual((), torch.amin(zero_d, dim=0, keepdim=False).shape)
        self.assertEqual((1,), torch.amin(one_d, dim=0, keepdim=True).shape)
        self.assertEqual((), torch.amin(one_d, dim=0, keepdim=False).shape)

        # set_
        zero_d_clone = zero_d.clone()
        one_d_clone = one_d.clone()
        self.assertEqual((), zero_d_clone.set_(one_d.storage(), 0, (), ()).shape)
        self.assertEqual((1,), zero_d_clone.set_(one_d.storage(), 0, (1,), (1,)).shape)
        self.assertEqual((), one_d_clone.set_(one_d.storage(), 0, (), ()).shape)
        self.assertEqual((1,), one_d_clone.set_(one_d.storage(), 0, (1,), (1,)).shape)

        self.assertEqual((), zero_d.clone().set_(zero_d).shape)
        self.assertEqual((), one_d.clone().set_(zero_d).shape)
        self.assertEqual((1,), zero_d.clone().set_(one_d).shape)
        self.assertEqual((1,), one_d.clone().set_(one_d).shape)

        # take
        self.assertEqual((), torch.randn((2, 3), device=device).take(zero_d_int).shape)
        self.assertEqual((1,), torch.randn((2, 3), device=device).take(one_d_int).shape)

        # gather
        self.assertEqual((), torch.gather(zero_d, 0, torch.zeros((), dtype=torch.int64, device=device)).shape)
        self.assertEqual((1,), torch.gather(zero_d, 0, torch.zeros((1,), dtype=torch.int64, device=device)).shape)
        self.assertEqual((), torch.gather(one_d, 0, torch.zeros((), dtype=torch.int64, device=device)).shape)
        self.assertEqual((1,), torch.gather(one_d, 0, torch.zeros((1,), dtype=torch.int64, device=device)).shape)

        # normal
        # std must be >= 0
        zero_d_ge_0 = torch.rand((), device=device)
        # documentation says out shape matches shape of mean
        self.assertEqual((), torch.normal(zero_d, zero_d_ge_0).shape)
        self.assertEqual((1,), torch.normal(one_d, zero_d_ge_0).shape)
        self.assertEqual((), torch.normal(1, zero_d_ge_0).shape)
        self.assertEqual((), torch.normal(zero_d, 1).shape)
        self.assertEqual((1,), torch.normal(one_d, 1).shape)
        # TODO: this behavior differs on CPU and GPU, see https://github.com/pytorch/pytorch/issues/30480.
        # self.assertEqual((), torch.normal(zero_d, one_d).shape)
        # self.assertEqual((), torch.normal(1, one_d).shape)

        # convolutions.  Yes, we are testing nn.functional here; seems justified
        # given its similar to the other tests
        w = torch.randn(2, 1, 3, 3, device=device).div_(2).requires_grad_()
        self.assertRaises(RuntimeError, lambda: torch.nn.functional.conv2d(zero_d, w, groups=1))
        self.assertRaises(RuntimeError, lambda: torch.nn.functional.conv2d(zero_d, w, groups=2))

        # nll_loss -- verify input can't be 0-dimensional.
        self.assertRaises(ValueError, lambda: torch.nn.functional.nll_loss(zero_d, zero_d, reduction='none'))
        self.assertRaises(ValueError, lambda: torch.nn.functional.nll_loss(zero_d, one_d, reduction='none'))
        # verify output is 0-dimensional when reduction != 'none'
        for (input, target) in ((torch.randn(1, 1, device=device), torch.tensor([0], device=device)),
                                (torch.randn(1, 1, 1, 1, device=device), torch.tensor([[[0]]], device=device))):
            self.assertEqual((), torch.nn.functional.nll_loss(input, target, reduction='mean').shape)
            self.assertEqual((), torch.nn.functional.nll_loss(input, target, reduction='sum').shape)