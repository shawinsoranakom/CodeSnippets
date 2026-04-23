def test_weights_parametrized(self):
        model = ModelUnderTest(bias=False)

        if hasattr(model.linear, "parametrizations"):
            raise AssertionError("model.linear should not have parametrizations")
        if hasattr(model.seq[0], "parametrizations"):
            raise AssertionError("model.seq[0] should not have parametrizations")
        if hasattr(model.seq[1], "parametrizations"):
            raise AssertionError("model.seq[1] should not have parametrizations")
        mask = torch.eye(16)
        parametrize.register_parametrization(
            model.linear, "weight", utils.FakeSparsity(mask)
        )
        mask = torch.eye(16)
        parametrize.register_parametrization(
            model.seq[0], "weight", utils.FakeSparsity(mask)
        )
        mask = torch.eye(16)
        parametrize.register_parametrization(
            model.seq[1], "weight", utils.FakeSparsity(mask)
        )

        if not hasattr(model.linear, "parametrizations"):
            raise AssertionError("model.linear should have parametrizations")
        if not parametrize.is_parametrized(model.linear, "weight"):
            raise AssertionError("model.linear.weight should be parametrized")
        if not hasattr(model.seq[0], "parametrizations"):
            raise AssertionError("model.seq[0] should have parametrizations")
        if not parametrize.is_parametrized(model.linear, "weight"):
            raise AssertionError("model.linear.weight should be parametrized")
        if not hasattr(model.seq[1], "parametrizations"):
            raise AssertionError("model.seq[1] should have parametrizations")
        if not parametrize.is_parametrized(model.linear, "weight"):
            raise AssertionError("model.linear.weight should be parametrized")