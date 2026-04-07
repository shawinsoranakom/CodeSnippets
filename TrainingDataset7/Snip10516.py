def get_concrete_model_key(self, model):
        (
            concrete_models_mapping,
            _,
        ) = self._get_concrete_models_mapping_and_proxy_models()
        model_key = make_model_tuple(model)
        return concrete_models_mapping[model_key]