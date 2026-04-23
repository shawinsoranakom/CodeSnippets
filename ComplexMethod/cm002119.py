def test_decorator_eager(self):
        """Test that the can_return_tuple decorator works with eager mode."""

        # test nothing is set
        config = PreTrainedConfig()
        model = self._get_model(config)
        inputs = torch.tensor(10)
        output = model(inputs)
        self.assertIsInstance(
            output, BaseModelOutput, "output should be a BaseModelOutput when return_dict is not set"
        )

        # test all explicit cases
        for config_return_dict in [True, False, None]:
            for return_dict in [True, False, None]:
                config = PreTrainedConfig(return_dict=config_return_dict)
                model = self._get_model(config)
                output = model(torch.tensor(10), return_dict=return_dict)

                expected_type = (
                    tuple
                    if return_dict is False
                    else (tuple if config_return_dict is False and return_dict is None else BaseModelOutput)
                )
                if config_return_dict is None and return_dict is None:
                    expected_type = tuple
                message = f"output should be a {expected_type.__name__} when config.return_dict={config_return_dict} and return_dict={return_dict}"
                self.assertIsInstance(output, expected_type, message)