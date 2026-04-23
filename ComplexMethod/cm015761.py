def test_prepare_config(self):
        model = SimpleLinear()
        sparsifier = ImplementedSparsifier(test=3)
        # Make sure there are no parametrizations before `prepare`
        if hasattr(model.seq[0], "parametrizations"):
            raise AssertionError("model.seq[0] should not have parametrizations")
        if hasattr(model.linear1, "parametrizations"):
            raise AssertionError("model.linear1 should not have parametrizations")
        if hasattr(model.linear2, "parametrizations"):
            raise AssertionError("model.linear2 should not have parametrizations")
        sparsifier.prepare(
            model,
            config=[
                {"tensor_fqn": "seq.0.weight", "test": 42},
                # No 'linear1' to make sure it will be skipped in the sparsification
                {"tensor_fqn": "linear2.weight"},
            ],
        )
        if len(sparsifier.groups) != 2:
            raise AssertionError(f"Expected 2 groups, got {len(sparsifier.groups)}")
        # Check if default argument is not assigned if explicit
        if sparsifier.groups[0]["tensor_fqn"] != "seq.0.weight":
            raise AssertionError(
                f"Expected tensor_fqn 'seq.0.weight', got {sparsifier.groups[0]['tensor_fqn']}"
            )
        if sparsifier.groups[0]["test"] != 42:
            raise AssertionError(
                f"Expected test value 42, got {sparsifier.groups[0]['test']}"
            )
        # Check if FQN and module are pointing to the same location
        if sparsifier.groups[1]["tensor_fqn"] != "linear2.weight":
            raise AssertionError(
                f"Expected tensor_fqn 'linear2.weight', got {sparsifier.groups[1]['tensor_fqn']}"
            )
        if sparsifier.groups[1]["module"] != model.linear2:
            raise AssertionError("Expected module to be model.linear2")
        # Check if parameterizations are attached
        if not hasattr(model.seq[0], "parametrizations"):
            raise AssertionError("model.seq[0] should have parametrizations")
        if hasattr(model.linear1, "parametrizations"):
            raise AssertionError("model.linear1 should not have parametrizations")
        if not hasattr(model.linear2, "parametrizations"):
            raise AssertionError("model.linear2 should have parametrizations")