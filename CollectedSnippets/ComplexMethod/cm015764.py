def test_mask_squash_with_params2(self):
        model = SimpleLinear()
        sparsifier = ImplementedSparsifier(foo=3, bar=2, baz=1)
        sparsifier.prepare(
            model, [{"tensor_fqn": "linear1.weight"}, {"tensor_fqn": "seq.0.weight"}]
        )
        sparsifier.squash_mask(params_to_keep=("foo", "bar"))
        if is_parametrized(model.seq[0], "weight"):
            raise AssertionError("Expected model.seq[0] to not be parametrized")
        if is_parametrized(model.linear1, "weight"):
            raise AssertionError("Expected model.linear1 to not be parametrized")
        if not hasattr(model.seq[0], "sparse_params"):
            raise AssertionError("Expected model.seq[0] to have sparse_params")
        if not hasattr(model.linear1, "sparse_params"):
            raise AssertionError("Expected model.linear1 to have sparse_params")
        if model.seq[0].sparse_params.get("foo", None) != 3:
            raise AssertionError(
                f"Expected seq[0].sparse_params['foo'] == 3, got {model.seq[0].sparse_params.get('foo', None)}"
            )
        if model.seq[0].sparse_params.get("bar", None) != 2:
            raise AssertionError(
                f"Expected seq[0].sparse_params['bar'] == 2, got {model.seq[0].sparse_params.get('bar', None)}"
            )
        if model.seq[0].sparse_params.get("baz", None) is not None:
            raise AssertionError("Expected seq[0].sparse_params['baz'] to be None")
        if model.linear1.sparse_params.get("foo", None) != 3:
            raise AssertionError(
                f"Expected linear1.sparse_params['foo'] == 3, got {model.linear1.sparse_params.get('foo', None)}"
            )
        if model.linear1.sparse_params.get("bar", None) != 2:
            raise AssertionError(
                f"Expected linear1.sparse_params['bar'] == 2, got {model.linear1.sparse_params.get('bar', None)}"
            )
        if model.linear1.sparse_params.get("baz", None) is not None:
            raise AssertionError("Expected linear1.sparse_params['baz'] to be None")