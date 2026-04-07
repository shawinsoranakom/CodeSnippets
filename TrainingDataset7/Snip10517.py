def _get_concrete_models_mapping_and_proxy_models(self):
        concrete_models_mapping = {}
        proxy_models = {}
        # Split models to proxy and concrete models.
        for model_key, model_state in self.models.items():
            if model_state.options.get("proxy"):
                proxy_models[model_key] = model_state
                # Find a concrete model for the proxy.
                concrete_models_mapping[model_key] = (
                    self._find_concrete_model_from_proxy(
                        proxy_models,
                        model_state,
                    )
                )
            else:
                concrete_models_mapping[model_key] = model_key
        return concrete_models_mapping, proxy_models