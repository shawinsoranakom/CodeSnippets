def resolve_fields_and_relations(self):
        # Resolve fields.
        for model_state in self.models.values():
            for field_name, field in model_state.fields.items():
                field.name = field_name
        # Resolve relations.
        # {remote_model_key: {model_key: {field_name: field}}}
        self._relations = defaultdict(partial(defaultdict, dict))
        concretes, proxies = self._get_concrete_models_mapping_and_proxy_models()

        for model_key in concretes:
            self.resolve_model_relations(model_key, concretes)

        for model_key in proxies:
            self._relations[model_key] = self._relations[concretes[model_key]]