def test_broadcast(self, fn, device):
        # functions with three tensor arguments
        fns_3_args = {"map2"}
        fns_value_kwarg = {"addcdiv", "addcmul"}

        (dims_small, dims_large, dims_full) = self._select_broadcastable_dims()
        full1d = torch.randn(*dims_full, device=device).flatten().float()
        small = torch.randn(*dims_small, device=device).float()
        large = torch.randn(*dims_large, device=device).float()
        small_expanded = small.expand(*dims_full)
        large_expanded = large.expand(*dims_full)
        small2 = None
        small2_expanded = None
        if fn in fns_3_args or fn in fns_value_kwarg:
            # create another smaller tensor
            (dims_small2, _, _) = self._select_broadcastable_dims(dims_full)
            small2 = torch.randn(*dims_small2, device=device).float()
            small2_expanded = small2.expand(*dims_full)

        if small.is_cuda and fn in ['map', 'map2']:
            # map and map2 are not implemented on CUDA tensors
            return

        if hasattr(large_expanded, fn):
            # run through tensor versions of functions
            # and verify fully expanded inputs give same results
            expanded = {large: large_expanded, small: small_expanded, small2: small2_expanded}

            def tensorfn(myfn, t1, t2):
                if fn == "lerp":
                    return myfn(t1, 0.5)
                elif fn == "masked_select":
                    return myfn(t1 < 0)
                elif fn == "masked_scatter":
                    return myfn(t1 < 0.5, full1d)
                elif fn == "masked_fill":
                    return myfn(t1 < 0.5, 1.0)
                elif fn in fns_3_args:
                    return myfn(1, t1, t2)
                elif fn in fns_value_kwarg:
                    return myfn(t1, t2, value=1)
                else:
                    return myfn(t1)

            # test various orders
            for first, second, third in [(large, small, small2), (small, large, small2),
                                         (small2, small, large), (small2, large, small)]:
                if first is None:
                    break  # ignore last iter when small2 is None
                method_expanded = getattr(expanded[first], fn)
                method = getattr(first, fn)
                r1 = tensorfn(method_expanded, expanded[second], expanded[third])
                r2 = tensorfn(method, second, third)
                self.assertEqual(r1, r2)

        # now for torch. versions of functions
        if hasattr(torch, fn):
            fntorch = getattr(torch, fn)
            expanded = {large: large_expanded, small: small_expanded, small2: small2_expanded}

            def torchfn(t1, t2, t3):
                if fn == "lerp":
                    return fntorch(t1, t2, 0.5)
                elif fn == "masked_select":
                    return fntorch(t1, t2 < 0)
                elif fn == "masked_scatter":
                    return fntorch(t1, t2 < 0.5, full1d)
                elif fn == "masked_fill":
                    return fntorch(t1, t2 < 0.5, 1.0)
                elif fn in fns_3_args:
                    return fntorch(t1, 1.0, t2, t3)
                elif fn in fns_value_kwarg:
                    return fntorch(t1, t2, t3, value=1.0)
                else:
                    return fntorch(t1, t2)

            # test various orders
            for first, second, third in [(large, small, small2), (small, large, small2),
                                         (small2, small, large), (small2, large, small)]:
                if first is None:
                    break  # ignore last iter when small2 is None
                r1 = torchfn(expanded[first], expanded[second], expanded[third])
                r2 = torchfn(first, second, third)
                self.assertEqual(r1, r2)

        # now for in place functions
        # in-place tensor is not broadcastable; test only guaranteed
        # to work by broadcasting other argument(s)
        if not hasattr(large_expanded, fn + "_"):
            return

        # need to clone largeExpanded so we can reuse, since functions are in-place
        large_expanded_clone = large_expanded.clone()

        def tensorfn_inplace(t0, t1, t2=None):
            t0_fn = getattr(t0, fn + "_")
            if fn == "lerp":
                return t0_fn(t1, 0.5)
            elif fn == "masked_scatter":
                return t0_fn(t1 < 0.5, full1d)
            elif fn == "masked_fill":
                return t0_fn(t1 < 0.5, 1.0)
            elif fn == "map":
                return t0_fn(t1, lambda x, y: x + y)
            elif fn == "map2":
                return t0_fn(t1, t2, lambda x, y, z: x + y + z)
            elif fn in fns_3_args:
                return t0_fn(1.0, t1, t2)
            elif fn in fns_value_kwarg:
                return t0_fn(t1, t2, value=1.0)
            else:
                return t0_fn(t1)
        # in-place pointwise operations don't actually work if the in-place
        # tensor is 0-strided (numpy has the same issue)
        if (0 not in large_expanded.stride() and 0 not in large_expanded_clone.stride()):
            r1 = tensorfn_inplace(large_expanded, small_expanded, small2_expanded)
            r2 = tensorfn_inplace(large_expanded_clone, small, small2)
            self.assertEqual(r1, r2)

        def broadcastable(t0, t1, t2=None):
            try:
                t1.expand_as(t0)
                if t2 is not None:
                    t2.expand_as(t0)
            except RuntimeError:
                return False
            return True

        def _test_in_place_broadcastable(t0, t1, t2=None):
            if not broadcastable(t0, t1, t2):
                same_size = t0.numel() == t1.numel() and (t0.numel() == t2.numel() if t2 is not None else True)
                if not same_size:
                    # Functionalization converts the inplace to an out-of-place, which causes us to error.
                    # We should fix this, but "error probably on bad inputs" isn't a hi-pri PT2 item.
                    if not TEST_WITH_TORCHINDUCTOR:
                        self.assertRaises(RuntimeError, lambda: tensorfn_inplace(t0, t1, t2))
            else:
                tensorfn_inplace(t0, t1, t2)

        if fn not in fns_3_args and fn not in fns_value_kwarg:
            _test_in_place_broadcastable(small, large_expanded)
            _test_in_place_broadcastable(small, large)
        else:
            _test_in_place_broadcastable(small2, small_expanded, large_expanded)
            _test_in_place_broadcastable(small2, small, large)