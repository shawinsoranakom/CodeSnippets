def get_foreign_related_value(self, instance):
        return self.get_instance_value_for_fields(instance, self.foreign_related_fields)