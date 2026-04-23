def _check_common(
        self,
        dot_prod_attention,
        args1=None,
        contains=True,
        atol=1e-3,
        has_fuse_pattern=True,
        has_dropout=False,
        check_train=True,
        override_check_equal=False,
        dtype=torch.float,
        rtol=0.2,
    ):
        if args1 is None:
            tensor_shape = (4, 2, 16, 32)
            args1 = [
                torch.randn(tensor_shape, device=self.device, dtype=dtype),
                torch.randn(tensor_shape, device=self.device, dtype=dtype),
                torch.randn(tensor_shape, device=self.device, dtype=dtype),
            ]
        else:
            args1 = list(args1)
        args2 = self._clone_inputs(args1)

        for training in [False, True] if check_train else [False]:
            if training and self.device == "xpu":
                # Intel GPU have not implemented sdpa backward yet mode.
                # TODO: remove this when sdpa backward is implemented for XPU.
                continue
            for x in itertools.chain(args1[:], args2[:]):
                if isinstance(x, torch.Tensor) and x.is_floating_point():
                    x.requires_grad = training

            if not self.use_static_shapes:
                for i in range(min(3, len(args2))):
                    if isinstance(args2[i], torch.Tensor):
                        torch._dynamo.mark_dynamic(args2[i], 0)

            dropout_arg = [training] if has_dropout else []
            torch.manual_seed(1234)
            result1 = dot_prod_attention(*(args1 + dropout_arg))

            counters.clear()
            torch.manual_seed(1234)
            result2, source_code = run_and_get_code(
                torch.compile(dot_prod_attention, fullgraph=True),
                *(args2 + dropout_arg),
            )
            source_code = "\n".join(source_code)
            if has_fuse_pattern:
                self.assertGreaterEqual(counters["inductor"]["fuse_attention"], 1)
            if contains:
                # many of the patterns get re-expanded in dispatcher
                self.assertIn(
                    "aten._scaled_dot_product",
                    source_code,
                )

            # some tests configured with very low dropout where we still want to check equality
            if not has_dropout or override_check_equal:
                self.assertEqual(result1, result2, atol=atol, rtol=rtol)

            if training:
                result1.sum().backward()
                result2.sum().backward()
                for arg1, arg2 in zip(args1, args2):
                    if (
                        isinstance(arg1, torch.Tensor)
                        and arg1.is_floating_point()
                        and (not has_dropout or override_check_equal)
                    ):
                        self.assertEqual(arg1.grad, arg2.grad, atol=atol, rtol=rtol)