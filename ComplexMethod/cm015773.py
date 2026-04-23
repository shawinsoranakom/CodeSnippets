def _test_constructor_on_device(self, model, device):
        self.assertRaisesRegex(
            TypeError,
            "BaseStructuredSparsifier.*update_mask",
            BaseStructuredSparsifier,
        )
        model1 = copy.deepcopy(model).to(device)
        pruner = SimplePruner(None)
        pruner.prepare(model1, None)
        pruner.enable_mask_update = True
        for g in pruner.groups:
            module = g["module"]
            if module.weight.device.type != device.type:
                raise AssertionError(
                    f"Expected device {device.type}, got {module.weight.device.type}"
                )
        if len(pruner.groups) != 5:
            raise AssertionError(f"Expected 5 groups, got {len(pruner.groups)}")
        pruner.step()
        # Can instantiate the model with configs
        model2 = copy.deepcopy(model).to(device)
        pruner = SimplePruner({"test": 3})
        pruner.prepare(model2, [{"tensor_fqn": "seq.0.weight"}])
        if len(pruner.groups) != 1:
            raise AssertionError(f"Expected 1 group, got {len(pruner.groups)}")
        if pruner.groups[0]["module_fqn"] != "seq.0":
            raise AssertionError(
                f"Expected module_fqn 'seq.0', got {pruner.groups[0]['module_fqn']}"
            )
        if "test" not in pruner.groups[0]:
            raise AssertionError("Expected 'test' key in pruner.groups[0]")
        if pruner.groups[0]["test"] != 3:
            raise AssertionError(
                f"Expected test value 3, got {pruner.groups[0]['test']}"
            )