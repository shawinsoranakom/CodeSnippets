def _check_on_fit_end(self, pl_module, callback, sparsifier_args):
        """Makes sure that each component of is working as expected while calling the
        post-training callback.
        Specifically, check the following -
            1. sparsifier config is the same as input config
            2. data sparsifier is correctly attached to the model
            3. sparsity is achieved after .step()
            4. non-sparsified values are the same as original values
        """
        callback.on_fit_end(42, pl_module)  # 42 is a dummy value

        # check sparsifier config
        for key, value in sparsifier_args.items():
            if callback.data_sparsifier.defaults[key] != value:
                raise AssertionError(
                    f"data_sparsifier.defaults[{key!r}] = {callback.data_sparsifier.defaults[key]}, expected {value}"
                )

        # assert that the model is correctly attached to the sparsifier
        for name, param in pl_module.model.named_parameters():
            valid_name = _get_valid_name(name)
            if type(param) not in SUPPORTED_TYPES:
                if valid_name in callback.data_sparsifier.state:
                    raise AssertionError(
                        f"valid_name {valid_name!r} should not be in data_sparsifier.state"
                    )
                if valid_name in callback.data_sparsifier.data_groups:
                    raise AssertionError(
                        f"valid_name {valid_name!r} should not be in data_sparsifier.data_groups"
                    )
                continue
            if valid_name not in callback.data_sparsifier.data_groups:
                raise AssertionError(
                    f"valid_name {valid_name!r} should be in data_sparsifier.data_groups"
                )
            if valid_name not in callback.data_sparsifier.state:
                raise AssertionError(
                    f"valid_name {valid_name!r} should be in data_sparsifier.state"
                )

            mask = callback.data_sparsifier.get_mask(name=valid_name)

            # assert that some level of sparsity is achieved
            sparsity = 1.0 - mask.float().mean()
            if not (sparsity > 0.0):
                raise AssertionError(f"expected sparsity > 0.0, got {sparsity}")

            # make sure that non-zero values in data after squash mask are equal to original values
            sparsified_data = callback.data_sparsifier.get_data(
                name=valid_name, return_original=False
            )
            if not torch.all(
                sparsified_data[sparsified_data != 0] == param[sparsified_data != 0]
            ):
                raise AssertionError(
                    "non-zero sparsified_data values do not match original param values"
                )