def rename_index(self, app_label, model_name, old_index_name, new_index_name):
        model_state = self.models[app_label, model_name]
        objs = model_state.options["indexes"]

        new_indexes = []
        for obj in objs:
            if obj.name == old_index_name:
                obj = obj.clone()
                obj.name = new_index_name
            new_indexes.append(obj)

        model_state.options["indexes"] = new_indexes
        self.reload_model(app_label, model_name, delay=True)