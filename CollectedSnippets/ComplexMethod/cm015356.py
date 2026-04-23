def test_invalid_log_probs_arg(self):
        # Check that validation errors are indeed disabled,
        # but they might raise another error
        for Dist, params in _get_examples():
            if Dist == TransformedDistribution:
                # TransformedDistribution has a distribution instance
                # as the argument, so we cannot do much about that
                continue
            for i, param in enumerate(params):
                d_nonval = Dist(validate_args=False, **param)
                d_val = Dist(validate_args=True, **param)
                for v in torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0]):
                    # samples with incorrect shape must throw ValueError only
                    try:
                        d_val.log_prob(v)
                    except ValueError:
                        pass
                    # get sample of correct shape
                    val = torch.full(d_val.batch_shape + d_val.event_shape, v)
                    # check samples with incorrect support
                    try:
                        d_val.log_prob(val)
                    except ValueError as e:
                        if e.args and "must be within the support" in e.args[0]:
                            try:
                                d_nonval.log_prob(val)
                            except RuntimeError:
                                pass

                # check correct samples are ok
                valid_value = d_val.sample()
                d_val.log_prob(valid_value)
                # check invalid values raise ValueError
                if valid_value.dtype == torch.long:
                    valid_value = valid_value.float()
                invalid_value = torch.full_like(valid_value, math.nan)
                try:
                    with self.assertRaisesRegex(
                        ValueError,
                        "Expected value argument .* to be within the support .*",
                    ):
                        d_val.log_prob(invalid_value)
                except AssertionError as e:
                    fail_string = "Support ValueError not raised for {} example {}/{}"
                    raise AssertionError(
                        fail_string.format(Dist.__name__, i + 1, len(params))
                    ) from e