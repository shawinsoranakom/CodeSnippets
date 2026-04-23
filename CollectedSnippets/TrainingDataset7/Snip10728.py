def clear_restricted_objects_from_set(self, model, objs):
        if model in self.restricted_objects:
            self.restricted_objects[model] = {
                field: items - objs
                for field, items in self.restricted_objects[model].items()
            }