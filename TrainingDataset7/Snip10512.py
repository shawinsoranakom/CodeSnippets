def update_model_field_relation(
        self,
        model,
        model_key,
        field_name,
        field,
        concretes,
    ):
        remote_model_key = resolve_relation(model, *model_key)
        if remote_model_key[0] not in self.real_apps and remote_model_key in concretes:
            remote_model_key = concretes[remote_model_key]
        relations_to_remote_model = self._relations[remote_model_key]
        if field_name in self.models[model_key].fields:
            # The assert holds because it's a new relation, or an altered
            # relation, in which case references have been removed by
            # alter_field().
            assert field_name not in relations_to_remote_model[model_key]
            relations_to_remote_model[model_key][field_name] = field
        else:
            del relations_to_remote_model[model_key][field_name]
            if not relations_to_remote_model[model_key]:
                del relations_to_remote_model[model_key]