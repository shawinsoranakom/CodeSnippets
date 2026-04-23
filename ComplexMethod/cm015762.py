def test_state_dict(self):
        step_count = 3
        model0 = SimpleLinear()
        sparsifier0 = ImplementedSparsifier(test=3)
        sparsifier0.prepare(model0, [{"tensor_fqn": "linear1.weight"}])
        mask = model0.linear1.parametrizations["weight"][0].mask
        mask.data = torch.arange(mask.shape[0] * mask.shape[1]).reshape(mask.shape)
        for _ in range(step_count):
            sparsifier0.step()
        state_dict = sparsifier0.state_dict()

        # Check the expected keys in the state_dict
        if "state" not in state_dict:
            raise AssertionError("Expected 'state' key in state_dict")
        if "step_count" not in state_dict["state"]["linear1.weight"]:
            raise AssertionError(
                "Expected 'step_count' in state_dict['state']['linear1.weight']"
            )
        if state_dict["state"]["linear1.weight"]["step_count"] != 3:
            raise AssertionError(
                f"Expected step_count 3, got {state_dict['state']['linear1.weight']['step_count']}"
            )
        if "groups" not in state_dict:
            raise AssertionError("Expected 'groups' key in state_dict")
        if "test" not in state_dict["groups"][0]:
            raise AssertionError("Expected 'test' key in state_dict['groups'][0]")
        if "tensor_fqn" not in state_dict["groups"][0]:
            raise AssertionError("Expected 'tensor_fqn' key in state_dict['groups'][0]")
        if state_dict["groups"][0]["tensor_fqn"] != "linear1.weight":
            raise AssertionError(
                f"Expected tensor_fqn 'linear1.weight', got {state_dict['groups'][0]['tensor_fqn']}"
            )

        # Check loading static_dict creates an equivalent model
        model1 = SimpleLinear()
        sparsifier1 = ImplementedSparsifier()
        sparsifier1.prepare(model1, None)

        if sparsifier0.state == sparsifier1.state:
            raise AssertionError("Expected sparsifier states to be different")

        # Make sure the masks are different in the beginning
        for mg in sparsifier0.groups:
            if mg["tensor_fqn"] == "linear1.weight":
                mask0 = mg["module"].parametrizations.weight[0].mask
        for mg in sparsifier1.groups:
            if mg["tensor_fqn"] == "linear1.weight":
                mask1 = mg["module"].parametrizations.weight[0].mask
        self.assertNotEqual(mask0, mask1)

        sparsifier1.load_state_dict(state_dict)

        # Make sure the states are loaded, and are correct
        if sparsifier0.state != sparsifier1.state:
            raise AssertionError("Expected sparsifier states to be equal after loading")

        # Make sure the masks (and all dicts) are the same after loading
        if len(sparsifier0.groups) != len(sparsifier1.groups):
            raise AssertionError(
                f"Expected equal group lengths, got {len(sparsifier0.groups)} and {len(sparsifier1.groups)}"
            )
        for idx in range(len(sparsifier0.groups)):
            mg0 = sparsifier0.groups[idx]
            mg1 = sparsifier1.groups[idx]
            for key in mg0:
                if key not in mg1:
                    raise AssertionError(f"Expected key '{key}' in mg1")
                if key == "module":
                    # We cannot compare modules as they are different
                    param0 = mg0[key].parametrizations.weight[0]
                    param1 = mg1[key].parametrizations.weight[0]
                    if not hasattr(param0, "mask"):
                        raise AssertionError("Expected param0 to have 'mask' attribute")
                    if not hasattr(param1, "mask"):
                        raise AssertionError("Expected param1 to have 'mask' attribute")
                    self.assertEqual(param0.__dict__, param1.__dict__)
                else:
                    if mg0[key] != mg1[key]:
                        raise AssertionError(
                            f"Expected mg0['{key}'] == mg1['{key}'], got {mg0[key]} != {mg1[key]}"
                        )