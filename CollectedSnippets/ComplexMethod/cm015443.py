def _test_replicate_transformer(self, sharding_strategy):
        model_args = ModelArgs()

        model = Transformer(model_args)
        replicate_model = deepcopy(model)

        for i, layer in enumerate(replicate_model.layers):
            if i % 2 == 0:
                replicate(layer)
            elif i % 2 == 1:
                fully_shard(layer)

        if sharding_strategy == "replicate":
            replicate_model = replicate(replicate_model)

        else:
            replicate_model = fully_shard(replicate_model)

        self._composable_api_module_check(replicate_model, sharding_strategy)

        for i, layer in enumerate(replicate_model.layers):
            if i % 2 == 0:
                self.assertTrue("replicate" in _get_registry(layer))
                for parameter in layer.parameters():
                    self.assertEqual(parameter.placements, (Replicate(),))
            elif i % 2 == 1:
                self.assertTrue("fully_shard" in _get_registry(layer))
                for parameter in layer.parameters():
                    self.assertEqual(parameter.placements, (Shard(dim=0),))