def get_pk_value_on_save(self, instance):
        values = []

        for field in self.fields:
            value = field.value_from_object(instance)
            if value is None:
                value = field.get_pk_value_on_save(instance)
            values.append(value)

        return tuple(values)