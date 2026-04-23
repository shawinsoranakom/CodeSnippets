def value_to_string(self, obj):
        values = []
        vals = self.value_from_object(obj)
        for field, value in zip(self.fields, vals):
            obj = AttributeSetter(field.attname, value)
            values.append(field.value_to_string(obj))
        return json.dumps(values, ensure_ascii=False)