def test_inference_mode_decorator(self):
        def func(x):
            self.assertEqual(torch.is_inference_mode_enabled(), mode)
            return x * x

        for mode, use_kwarg in product((True, False, None), (True, False)):
            if mode is None:
                if use_kwarg:
                    decorated = torch.inference_mode(mode=func)
                else:
                    decorated = torch.inference_mode(func)
                mode = True
            else:
                if use_kwarg:
                    decorated = torch.inference_mode(mode=mode)(func)
                else:
                    decorated = torch.inference_mode(mode)(func)

            for requires_grad in (True, False):
                c = torch.ones(1, 2, 3, requires_grad=requires_grad)
                d = decorated(c)
                self.assertTrue(not mode or torch.is_inference(d))
                self.assertEqual(d.requires_grad, requires_grad and not mode)