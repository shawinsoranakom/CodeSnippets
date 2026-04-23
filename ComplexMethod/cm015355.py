def test_params_constraints(self):
        normalize_probs_dists = (
            Categorical,
            Multinomial,
            OneHotCategorical,
            OneHotCategoricalStraightThrough,
            RelaxedOneHotCategorical,
        )

        for Dist, params in _get_examples():
            for i, param in enumerate(params):
                dist = Dist(**param)
                for name, value in param.items():
                    if isinstance(value, numbers.Number):
                        value = torch.tensor([value])
                    if Dist in normalize_probs_dists and name == "probs":
                        # These distributions accept positive probs, but elsewhere we
                        # use a stricter constraint to the simplex.
                        value = value / value.sum(-1, True)
                    try:
                        constraint = dist.arg_constraints[name]
                    except KeyError:
                        continue  # ignore optional parameters

                    # Check param shape is compatible with distribution shape.
                    self.assertGreaterEqual(value.dim(), constraint.event_dim)
                    value_batch_shape = value.shape[
                        : value.dim() - constraint.event_dim
                    ]
                    torch.broadcast_shapes(dist.batch_shape, value_batch_shape)

                    if is_dependent(constraint):
                        continue

                    message = f"{Dist.__name__} example {i + 1}/{len(params)} parameter {name} = {value}"
                    self.assertTrue(constraint.check(value).all(), msg=message)