def value_to_string(self, obj):
        return json.dumps(self.value_from_object(obj), ensure_ascii=False)