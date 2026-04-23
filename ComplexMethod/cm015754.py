def _check_state_dict(self, sparsifier1):
        """Checks if loading and restoring of state_dict() works as expected.
        Basically, dumps the state of the sparsifier and loads it in the other sparsifier
        and checks if all the configuration are in line.

        This function is called at various times in the workflow to makes sure that the sparsifier
        can be dumped and restored at any point in time.
        """
        state_dict = sparsifier1.state_dict()

        new_model = Model()

        # create an empty new sparsifier
        sparsifier2 = ActivationSparsifier(new_model)

        if sparsifier2.defaults == sparsifier1.defaults:
            raise AssertionError(
                "Expected sparsifier defaults to be different before load"
            )
        if len(sparsifier2.data_groups) == len(sparsifier1.data_groups):
            raise AssertionError(
                "Expected data_groups lengths to be different before load"
            )

        sparsifier2.load_state_dict(state_dict)

        if sparsifier2.defaults != sparsifier1.defaults:
            raise AssertionError("Expected sparsifier defaults to match after load")

        for name, state in sparsifier2.state.items():
            if name not in sparsifier1.state:
                raise AssertionError(f"Expected '{name}' in sparsifier1.state")
            mask1 = sparsifier1.state[name]["mask"]
            mask2 = state["mask"]

            if mask1 is None:
                if mask2 is not None:
                    raise AssertionError("Expected mask2 to be None when mask1 is None")
            else:
                if type(mask1) is not type(mask2):
                    raise AssertionError(
                        f"Expected same mask types, got {type(mask1)} and {type(mask2)}"
                    )
                if isinstance(mask1, list):
                    if len(mask1) != len(mask2):
                        raise AssertionError(
                            f"Expected mask lengths to match, got {len(mask1)} and {len(mask2)}"
                        )
                    for idx in range(len(mask1)):
                        if not torch.all(mask1[idx] == mask2[idx]):
                            raise AssertionError(f"Masks at index {idx} do not match")
                else:
                    if not torch.all(mask1 == mask2):
                        raise AssertionError("Masks do not match")

        # make sure that the state dict is stored as torch sparse
        for state in state_dict["state"].values():
            mask = state["mask"]
            if mask is not None:
                if isinstance(mask, list):
                    for idx in range(len(mask)):
                        if not mask[idx].is_sparse:
                            raise AssertionError(f"Expected mask[{idx}] to be sparse")
                else:
                    if not mask.is_sparse:
                        raise AssertionError("Expected mask to be sparse")

        dg1, dg2 = sparsifier1.data_groups, sparsifier2.data_groups

        for layer_name, config in dg1.items():
            if layer_name not in dg2:
                raise AssertionError(f"Expected '{layer_name}' in dg2")

            # exclude hook and layer
            config1 = {
                key: value
                for key, value in config.items()
                if key not in ["hook", "layer"]
            }
            config2 = {
                key: value
                for key, value in dg2[layer_name].items()
                if key not in ["hook", "layer"]
            }

            if config1 != config2:
                raise AssertionError(f"Configs for '{layer_name}' do not match")