def load_weights(self, weights: Iterable[tuple[str, torch.Tensor]]):
            params_dict = dict(self.named_parameters())

            # We support loading from both `*ForCausalLM` and `*Model`
            candidate_prefixes = ["", "model."]
            target_prefix = ""

            seen_weights = list[tuple[str, torch.Tensor]]()
            for name, loaded_weight in weights:
                # Clone because the iterator may reuse the tensor buffer
                seen_weights.append((name, loaded_weight.clone()))

                try:
                    target_prefix = next(
                        prefix
                        for prefix in candidate_prefixes
                        if prefix + name in params_dict
                    )
                    break
                except StopIteration:
                    # The weight might not exist on the model
                    # (to be handled by AutoWeightsLoader)
                    pass

            if target_prefix:
                target_model = self
                for attr in target_prefix.split("."):
                    if attr:
                        target_model = getattr(self, attr)

                logger.info(
                    "Mapping weights to %s as they are "
                    "relative to this model instead of %s.",
                    target_model._get_name(),
                    self._get_name(),
                )

            # Lazy chain so buffer-reusing weight iterators (e.g.
            # runai_streamer) are consumed one tensor at a time.
            mapped_weights = (
                (target_prefix + name, weight)
                for name, weight in itertools.chain(seen_weights, weights)
            )

            def default_load_weights(weights):
                loader = AutoWeightsLoader(self)
                return loader.load_weights(weights)

            load_weights = getattr(super(), "load_weights", default_load_weights)
            return load_weights(mapped_weights)