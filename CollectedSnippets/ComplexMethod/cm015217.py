def test_fails_with_autograd_function(self, device, transform):
        failed_build_envs = ("linux-focal-py3.8-clang10", "linux-focal-py3.11-clang10")
        if (
            device == "cpu"
            and transform in ["grad", "vmap"]
            and TEST_WITH_TORCHDYNAMO
            and os.getenv("BUILD_ENVIRONMENT", "") in failed_build_envs
        ):
            raise unittest.SkipTest(
                "Unexpected successes on focal with dynamo,"
                + " see https://github.com/pytorch/pytorch/issues/107173"
            )

        class Test(torch.autograd.Function):
            @staticmethod
            def forward(_, input):
                return input

            @staticmethod
            def backward(_, grad_input):
                return grad_input

        transform = getattr(functorch, transform)

        def f(x):
            return Test.apply(x)

        if transform in (grad, grad_and_value):
            input = torch.tensor(4.0)
        else:
            input = torch.randn(5)

        if transform is vjp:
            transform = functools.partial(transform, f)
        elif transform is jvp:
            input = (input,)
            transform = functools.partial(transform, f, input)
        else:
            transform = transform(f)

        with self.assertRaisesRegex(RuntimeError, "autograd.Function"):
            transform(input)