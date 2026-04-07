def resolve_model_field_relations(
        self,
        model_key,
        field_name,
        field,
        concretes=None,
    ):
        remote_field = field.remote_field
        if not remote_field:
            return
        if concretes is None:
            concretes, _ = self._get_concrete_models_mapping_and_proxy_models()

        self.update_model_field_relation(
            remote_field.model,
            model_key,
            field_name,
            field,
            concretes,
        )

        through = getattr(remote_field, "through", None)
        if not through:
            return
        self.update_model_field_relation(
            through, model_key, field_name, field, concretes
        )