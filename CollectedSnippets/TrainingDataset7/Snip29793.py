def create_json_data(field_value, array_field_value):
        fields = {
            "field": json.dumps(field_value, ensure_ascii=False),
            "array_field": json.dumps(
                [json.dumps(item, ensure_ascii=False) for item in array_field_value],
                ensure_ascii=False,
            ),
        }
        return json.dumps(
            [{"model": "postgres_tests.hstoremodel", "pk": None, "fields": fields}]
        )