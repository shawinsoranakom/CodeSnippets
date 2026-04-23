def test_disable_forced_specializations_ok(self):
        # check that we don't force specialization, and defer to runtime asserts
        # with prefer_deferred_runtime_asserts_over_guards=True to successfully export
        # case 1: modulo guards
        from torch.export import dims

        class Mod4Reshape(torch.nn.Module):
            def forward(self, x):
                return x.reshape(x.shape[0] - 1, 4, -1)  # Mod(s0*s1, 4*(s0-1)) = 0

        inputs = (torch.randn(10, 72),)
        dx, dy = dims("dx", "dy")
        for use_new_tracer in [True, False]:
            with torch._export.config.patch(use_new_tracer_experimental=use_new_tracer):
                ep = torch.export._trace._export(
                    Mod4Reshape(),
                    inputs,
                    dynamic_shapes={"x": (dx, dy)},
                    prefer_deferred_runtime_asserts_over_guards=True,
                    pre_dispatch=True,
                )
            out1 = ep.module()(torch.randn(8, 7))
            self.assertEqual(out1.shape, torch.ones(7, 4, 2).shape)
            out2 = ep.module()(torch.randn(12, 11))
            self.assertEqual(out2.shape, torch.ones(11, 4, 3).shape)
            with self.assertRaisesRegex(
                RuntimeError,
                r"^Runtime assertion failed for expression Eq\(Mod\(s\d+\*s\d+, 4\*s\d+\s*-\s*4\), 0\) on node 'eq[^']*'$",
            ):
                ep.module()(torch.randn(8, 8))  # fail

        # case 2: 2d reshape
        class FreeReshape(torch.nn.Module):
            def forward(self, x, y, z):
                return x.reshape([-1]) + y.reshape([-1]) + z  # s0*s1 = s2*s3 = s4

        inputs = (
            torch.randn(6, 8),
            torch.randn(3, 16),
            torch.randn(48),
        )
        dynamic_shapes = {
            "x": [Dim(f"dx{i}", min=2) for i in range(2)],
            "y": [Dim(f"dy{i}", min=2) for i in range(2)],
            "z": [Dim(f"dz{i}", min=4) for i in range(1)],
        }

        for private_api in (True, False):
            if private_api:
                ep = torch.export.export(
                    FreeReshape(),
                    inputs,
                    dynamic_shapes=dynamic_shapes,
                    prefer_deferred_runtime_asserts_over_guards=True,
                )
            else:
                ep = export(FreeReshape(), inputs, dynamic_shapes=dynamic_shapes)
            out1 = ep.module()(torch.randn(48, 1), torch.randn(4, 12), torch.randn(48))
            self.assertEqual(out1.shape, torch.ones(48).shape)
            out2 = ep.module()(torch.randn(5, 8), torch.randn(4, 10), torch.randn(40))
            self.assertEqual(out2.shape, torch.ones(40).shape)
            if private_api:
                with self.assertRaisesRegex(
                    RuntimeError,
                    r"Runtime assertion failed for expression Eq\((.*)\) on node '.*'",
                ):  # fail only at runtime
                    ep.module()(
                        torch.randn(5, 8), torch.randn(4, 5), torch.randn(30)
                    )  # fail
            else:
                # no runtime assert in exported module but it fails anyway with wrong inputs
                with self.assertRaisesRegex(
                    AssertionError,
                    escape(
                        "Guard failed: x.size()[1] * x.size()[0] == y.size()[0] * y.size()[1]"
                    ),
                ):
                    # expected 40, but got 20
                    ep.module()(torch.randn(5, 8), torch.randn(4, 5), torch.randn(30))

        # case 3: 3d reshape (previously failing with different issue)
        class Reshape3d(torch.nn.Module):
            def forward(self, x, y):
                return x.reshape([-1]) + y  # s0*s1*s2 = s3

        inputs = (
            torch.randn(4, 3, 2),
            torch.randn(24),
        )
        dynamic_shapes = {
            "x": (Dim("dx0", min=2), Dim("dx1", min=2), Dim("dx2", min=2)),
            "y": (Dim("dy", min=8),),
        }
        ep = torch.export.export(
            Reshape3d(),
            inputs,
            dynamic_shapes=dynamic_shapes,
            prefer_deferred_runtime_asserts_over_guards=True,
        )
        out1 = ep.module()(torch.randn(9, 7, 2), torch.randn(126))
        self.assertEqual(out1.shape, torch.ones(126).shape)
        with self.assertRaisesRegex(
            RuntimeError,
            r"Runtime assertion failed for expression Eq\((.*)\) on node '.*'",
        ):  # fail only at runtime
            ep.module()(torch.randn(4, 3, 2), torch.randn(10))