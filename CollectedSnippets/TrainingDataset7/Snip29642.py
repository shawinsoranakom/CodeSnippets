def create_json_data(array_field_value):
        fields = {"field": json.dumps(array_field_value, ensure_ascii=False)}
        return json.dumps(
            [{"model": "postgres_tests.chararraymodel", "pk": None, "fields": fields}]
        )