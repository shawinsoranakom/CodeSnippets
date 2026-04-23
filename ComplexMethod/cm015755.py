def check_state_dict(self, data_list, data_with_config, defaults, **kwargs):
        sparsifier1 = self._make_sparsifier(
            data_list, data_with_config, defaults=defaults, **kwargs
        )
        sparsifier2 = self._make_sparsifier(
            data_list=[data_list[0]], data_with_config=[], defaults=defaults, **kwargs
        )
        sparsifier1.step()

        state_dict1 = sparsifier1.state_dict()

        if sparsifier1.state == sparsifier2.state:
            raise AssertionError("Expected sparsifier states to be different")
        name, _, _ = self._get_name_data_config(data_list[0])
        self.assertNotEqual(sparsifier1.get_mask(name), sparsifier2.get_mask(name))

        sparsifier2.load_state_dict(state_dict1)
        if len(sparsifier1.state) != len(sparsifier2.state):
            raise AssertionError(
                f"Expected state lengths to match, got {len(sparsifier1.state)} vs {len(sparsifier2.state)}"
            )
        if len(sparsifier1.data_groups) != len(sparsifier2.data_groups):
            raise AssertionError(
                f"Expected data_groups lengths to match, got {len(sparsifier1.data_groups)} vs {len(sparsifier2.data_groups)}"
            )

        state1 = state_dict1["state"]
        for name in state1:
            # compare mask
            if name not in sparsifier2.state:
                raise AssertionError(f"Expected '{name}' in sparsifier2.state")
            if "mask" not in sparsifier2.state[name]:
                raise AssertionError(f"Expected 'mask' in sparsifier2.state['{name}']")
            if "mask" not in sparsifier1.state[name]:
                raise AssertionError(f"Expected 'mask' in sparsifier1.state['{name}']")
            mask1, mask2 = state1[name]["mask"], sparsifier2.state[name]["mask"]
            if not (mask1.is_sparse and not mask2.is_sparse):
                raise AssertionError(
                    "Expected mask1 to be sparse and mask2 to be dense"
                )
            if not torch.all(mask1.to_dense() == mask2):
                raise AssertionError("Masks do not match after loading state dict")

            # compare data_groups
            dg1, dg2 = sparsifier1.data_groups, sparsifier2.data_groups
            if not (name in dg1 and name in dg2):
                raise AssertionError(f"Expected '{name}' in both data_groups")
            if dg1[name] != dg2[name]:
                raise AssertionError(f"data_groups['{name}'] do not match")

            # compare container
            container1, container2 = sparsifier1._container, sparsifier2._container
            if not torch.all(getattr(container1, name) == getattr(container2, name)):
                raise AssertionError(f"Container data for '{name}' do not match")
            if is_parametrized(container1, name) != is_parametrized(container2, name):
                raise AssertionError(f"Parametrization state for '{name}' do not match")
            if is_parametrized(container1, name):
                param1 = getattr(container1.parametrizations, name)[0]
                param2 = getattr(container2.parametrizations, name)[0]
                if not hasattr(param1, "mask"):
                    raise AssertionError("Expected param1 to have 'mask' attribute")
                if not hasattr(param2, "mask"):
                    raise AssertionError("Expected param2 to have 'mask' attribute")
                self.assertEqual(param1.__dict__, param2.__dict__)