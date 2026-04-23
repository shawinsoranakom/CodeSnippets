def test_export_api_with_dynamic_shapes(self):
        from torch.export import Dim, dims

        # pass dynamic shapes of inputs [args]
        class Foo(torch.nn.Module):
            def forward(self, x, y):
                return torch.matmul(x, y)

        foo = Foo()
        inputs = (torch.randn(10, 2, 3), torch.randn(10, 3, 4))
        batch = Dim("batch")
        efoo = export(
            foo,
            inputs,
            dynamic_shapes={k: {0: batch} for k in ["x", "y"]},
        )
        self.assertEqual(efoo.module()(*inputs).shape, foo(*inputs).shape)

        foo = Foo()
        inputs = (torch.randn(10, 2, 3),)
        kwinputs = {"y": torch.randn(10, 3, 4)}
        batch = Dim("batch")
        efoo = export(
            foo, inputs, kwinputs, dynamic_shapes={k: {0: batch} for k in ["x", "y"]}
        )
        self.assertEqual(
            efoo.module()(*inputs, **kwinputs).shape, foo(*inputs, **kwinputs).shape
        )

        # pass dynamic shapes of inputs [partial, error]
        foo = Foo()
        inputs = (torch.randn(10, 2, 3),)
        kwinputs = {"y": torch.randn(10, 3, 4)}
        batch = Dim("batch")
        with self.assertRaisesRegex(
            torch._dynamo.exc.UserError,
            (
                "You marked.*but your code specialized it to be a constant.*"
                "If you're using Dim.DYNAMIC, replace it with either Dim.STATIC or Dim.AUTO(.*\n)*.*"
                "Suggested fixes:(.*\n)*.*"
                "batch = 10"
            ),
        ):
            export(
                foo,
                inputs,
                kwinputs,
                dynamic_shapes={"x": {0: batch}, "y": None},
            )

        # pass dynamic shapes of inputs [module]
        foo = Foo()
        inputs = (torch.randn(10, 2, 3), torch.randn(10, 3, 4))
        batch = Dim("batch")
        efoo = export(
            foo,
            inputs,
            dynamic_shapes={"x": {0: batch}, "y": {0: batch}},
        )
        self.assertEqual(efoo.module()(*inputs).shape, foo(*inputs).shape)

        # pass dynamic shapes of inputs [bounds, mostly shared]
        foo = Foo()
        inputs = (torch.randn(10, 3, 3), torch.randn(10, 3, 3))
        batch = Dim("batch", min=8, max=64)
        size = Dim("size")
        efoo = export(
            foo,
            inputs,
            dynamic_shapes={
                "x": (batch, size, size),
                "y": (batch, size, size),
            },
        )

        for node in efoo.graph_module.graph.nodes:
            if node.op == "placeholder":
                self.assertEqual(node.meta["val"].shape[1], node.meta["val"].shape[2])
        self.assertEqual(efoo.module()(*inputs).shape, foo(*inputs).shape)

        # pass dynamic shapes of inputs [multiple, mostly distinct]
        inputs = (torch.randn(10, 2, 3), torch.randn(10, 3, 4))
        batch, M, K, N = dims("batch", "M", "K", "N")
        efoo = export(
            Foo(),
            inputs,
            dynamic_shapes={"x": (batch, M, K), "y": (batch, K, N)},
        )
        placeholders = [
            node.meta["val"].shape
            for node in efoo.graph_module.graph.nodes
            if node.op == "placeholder"
        ]
        self.assertEqual(
            placeholders[0][2],
            placeholders[1][1],
        )
        self.assertEqual(efoo.module()(*inputs).shape, foo(*inputs).shape)

        # pass dynamic shapes of inputs [dict]
        class Foo(torch.nn.Module):
            def forward(self, inputs):
                return torch.matmul(inputs["x"], inputs["y"])

        foo = Foo()
        inputs = ({"x": torch.randn(10, 2, 3), "y": torch.randn(10, 3, 4)},)
        batch = Dim("batch")
        efoo = export(
            foo, inputs, dynamic_shapes={"inputs": {k: {0: batch} for k in ["x", "y"]}}
        )
        self.assertEqual(
            [
                # First dimension varies across strict and non-strict
                # since the source names are different, resulting in
                # different symbol names.
                str(node.meta["val"].shape[1:])
                for node in efoo.graph_module.graph.nodes
                if node.op == "placeholder"
            ],
            ["torch.Size([2, 3])", "torch.Size([3, 4])"],
        )
        self.assertEqual(efoo.module()(*inputs).shape, foo(*inputs).shape)

        # pass dynamic shapes of inputs [list]
        class Foo(torch.nn.Module):
            def forward(self, inputs):
                return torch.matmul(inputs[0], inputs[1])

        foo = Foo()
        inputs = ([torch.randn(10, 2, 3), torch.randn(10, 3, 4)],)
        batch = Dim("batch")
        efoo = export(
            foo, inputs, dynamic_shapes={"inputs": [{0: batch} for _ in range(2)]}
        )
        self.assertEqual(
            [
                # First dimension varies across strict and non-strict
                # since the source names are different, resulting in
                # different symbol names.
                str(node.meta["val"].shape[1:])
                for node in efoo.graph_module.graph.nodes
                if node.op == "placeholder"
            ],
            ["torch.Size([2, 3])", "torch.Size([3, 4])"],
        )
        self.assertEqual(efoo.module()(*inputs).shape, foo(*inputs).shape)

        # pass dynamic shapes of inputs [pytree-registered classes]
        if HAS_TORCHREC:
            # skipping tests if torchrec not available
            class Foo(torch.nn.Module):
                def forward(self, kjt) -> torch.Tensor:
                    return kjt.values() + 0, kjt.offsets() + 0

            foo = Foo()
            kjt = KeyedJaggedTensor(
                values=torch.Tensor([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
                keys=["index_0", "index_1"],
                lengths=torch.IntTensor([0, 2, 0, 1, 1, 1, 0, 3]),
                offsets=torch.IntTensor([0, 0, 2, 2, 3, 4, 5, 5, 8]),
            )
            inputs = (kjt,)
            dim = Dim("dim")
            dim_plus_one = Dim("dim_plus_one")
            efoo = torch.export.export(
                foo,
                inputs,
                dynamic_shapes={
                    "kjt": [{0: dim}, None, {0: dim}, {0: dim_plus_one}, None, None]
                },
            )
            self.assertEqual(
                [out.shape for out in efoo.module()(*inputs)],
                [out.shape for out in foo(*inputs)],
            )

        # pass dynamic shapes of inputs [distinct, error]
        class Foo(torch.nn.Module):
            def forward(self, x, y):
                return torch.matmul(x, y)

        foo = Foo()
        inputs = (torch.randn(10, 2, 3), torch.randn(10, 3, 4))
        batch, M, K1, K2, N = dims("batch", "M", "K1", "K2", "N")
        with self.assertRaisesRegex(
            torch._dynamo.exc.UserError,
            (
                "Constraints violated \\(K2\\)!(.*\n)*.*"
                "K2.*and.*K1.*must always be equal(.*\n)*.*"
                "Suggested fixes:(.*\n)*.*"
                "K2 = K1"
            ),
        ):
            export(
                foo,
                inputs,
                dynamic_shapes={"x": (batch, M, K1), "y": (batch, K2, N)},
            )

        # pass dynamic shapes of inputs [specialized, error]
        foo = Foo()
        inputs = (torch.randn(10, 2, 3), torch.randn(10, 3, 4))
        batch, M, K1, N = dims("batch", "M", "K1", "N")
        with self.assertRaisesRegex(
            torch._dynamo.exc.UserError,
            (
                "You marked.*but your code specialized it to be a constant.*"
                "If you're using Dim.DYNAMIC, replace it with either Dim.STATIC or Dim.AUTO(.*\n)*"
                "Suggested fixes:(.*\n)*.*"
                "K1 = 3"
            ),
        ):
            export(
                foo,
                inputs,
                dynamic_shapes={"x": (batch, M, K1), "y": (batch, None, N)},
            )

        # pass dynamic shapes of inputs [guards, error]
        class Foo(torch.nn.Module):
            def forward(self, x, y):
                if x.shape[0] < 16 and y.shape[1] % 3 == 0:
                    return torch.matmul(x, y)
                else:
                    return x + y

        foo = Foo()
        inputs = (torch.randn(10, 2, 3), torch.randn(10, 3, 4))
        batch, M, K, N = dims("batch", "M", "K", "N")
        with self.assertRaisesRegex(
            torch._dynamo.exc.UserError,
            (
                "Constraints violated.*!(.*\n)*.*"
                "Not all values of K.*satisfy the generated guard(.*\n)*.*"
                "Not all values of batch.*satisfy the generated guard(.*\n)*.*"
                "Suggested fixes:(.*\n)*.*"
                "batch = Dim\\('batch', max=15\\)(.*\n)*.*"
                "K = 3\\*_K"
            ),
        ):
            export(
                foo,
                inputs,
                dynamic_shapes={"x": (batch, M, K), "y": (batch, K, N)},
            )