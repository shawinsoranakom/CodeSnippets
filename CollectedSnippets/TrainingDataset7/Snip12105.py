def get_instance_lookups(self):
        class_lookups = self.get_class_lookups()
        if instance_lookups := getattr(self, "instance_lookups", None):
            return {**class_lookups, **instance_lookups}
        return class_lookups