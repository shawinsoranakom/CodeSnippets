def resolve_model_relations(self, model_key, concretes=None):
        if concretes is None:
            concretes, _ = self._get_concrete_models_mapping_and_proxy_models()

        model_state = self.models[model_key]
        for field_name, field in model_state.fields.items():
            self.resolve_model_field_relations(model_key, field_name, field, concretes)