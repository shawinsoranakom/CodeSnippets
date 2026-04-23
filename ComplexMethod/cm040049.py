def get_random_transformation(self, data, training=True, seed=None):
        if not training:
            return None

        if backend_utils.in_tf_graph():
            self.backend.set_backend("tensorflow")

            for layer_name in self._augment_layers:
                augmentation_layer = getattr(self, layer_name)
                augmentation_layer.backend.set_backend("tensorflow")

        seed = seed or self._get_seed_generator(self.backend._backend)

        chain_mixing_weights = self._sample_from_dirichlet(
            [self.num_chains], self.alpha, seed
        )
        weight_sample = self.backend.random.beta(
            shape=(),
            alpha=self.alpha,
            beta=self.alpha,
            seed=seed,
        )

        chain_transforms = []
        for _ in range(self.num_chains):
            depth_transforms = []
            for _ in range(self.chain_depth):
                layer_name = py_random.choice(self._augment_layers + [None])
                if layer_name is None:
                    continue
                augmentation_layer = getattr(self, layer_name)
                depth_transforms.append(
                    {
                        "layer_name": layer_name,
                        "transformation": (
                            augmentation_layer.get_random_transformation(
                                data,
                                seed=self._get_seed_generator(
                                    self.backend._backend
                                ),
                            )
                        ),
                    }
                )
            chain_transforms.append(depth_transforms)

        transformation = {
            "chain_mixing_weights": chain_mixing_weights,
            "weight_sample": weight_sample,
            "chain_transforms": chain_transforms,
        }

        return transformation