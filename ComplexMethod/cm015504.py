def test_apply_activation_checkpointing(self):
        """
        Ensures that `apply_activation_checkpointing` can be used
        to swap modules for their checkpoint-wrapped counterparts given
        a model.
        """

        class LinearWithBatchNorm(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.lin = nn.Linear(10, 10)
                self.bn = nn.BatchNorm1d(10)
                self.nested_linear = nn.Sequential(nn.Linear(10, 10))

            def forward(self, x):
                return self.bn(self.nested_linear(self.lin(x)))

        class MyModel(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.seq = nn.Sequential(
                    LinearWithBatchNorm(), LinearWithBatchNorm(), LinearWithBatchNorm()
                )

            def forward(self, x):
                return self.seq(x)

        def check_fn(l):
            return isinstance(l, nn.Linear)

        n_linear = None

        for i, wrapper in enumerate(
            [
                partial(checkpoint_wrapper, checkpoint_impl=CheckpointImpl.REENTRANT),
                partial(
                    checkpoint_wrapper, checkpoint_impl=CheckpointImpl.NO_REENTRANT
                ),
                offload_wrapper,
            ]
        ):
            model = MyModel()
            if n_linear is None:
                n_linear = sum(
                    1 if isinstance(x, nn.Linear) else 0 for x in model.modules()
                )

            with self.subTest(wrapper=wrapper):
                if i != 0:
                    apply_activation_checkpointing(
                        model, checkpoint_wrapper_fn=wrapper, check_fn=check_fn
                    )
                else:
                    apply_activation_checkpointing(
                        model,
                        checkpoint_wrapper_fn=wrapper,
                        auto_wrap_policy=ModuleWrapPolicy({nn.Linear}),
                    )
                n_linear_wrapped = sum(
                    1 if isinstance(x, nn.Linear) else 0 for x in model.modules()
                )
                n_checkpointed = sum(
                    1 if isinstance(x, (CheckpointWrapper, OffloadWrapper)) else 0
                    for x in model.modules()
                )
                self.assertEqual(n_checkpointed, n_linear_wrapped)
                self.assertEqual(n_linear, n_linear_wrapped)
                for j in range(3):
                    self.assertTrue(
                        isinstance(
                            model.seq[j].lin, (CheckpointWrapper, OffloadWrapper)
                        )
                    )
                    self.assertTrue(
                        isinstance(
                            model.seq[j].nested_linear[0],
                            (CheckpointWrapper, OffloadWrapper),
                        )
                    )

                inp = torch.randn(4, 10, requires_grad=True)
                for _ in range(6):
                    # Kwarg input
                    loss = model(x=inp).sum()
                    self.assertTrue(loss.requires_grad)
                    loss.backward()
                    # ensure checkpointed part of model has gradients
                    for j in range(3):
                        weight_lin = model.seq[j].lin._checkpoint_wrapped_module.weight
                        bias_lin = model.seq[j].lin._checkpoint_wrapped_module.bias
                        weight_nested_lin = (
                            model.seq[j]
                            .nested_linear[0]
                            ._checkpoint_wrapped_module.weight
                        )
                        bias_nested_lin = (
                            model.seq[j]
                            .nested_linear[0]
                            ._checkpoint_wrapped_module.bias
                        )
                        for param in [
                            weight_lin,
                            bias_lin,
                            weight_nested_lin,
                            bias_nested_lin,
                        ]:
                            self.assertTrue(param.requires_grad)
                            self.assertFalse(param.grad is None)