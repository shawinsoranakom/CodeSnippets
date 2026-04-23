def test_update_jsonfield_case_when_key_is_null(self):
        obj = JSONFieldModel.objects.create(data={"key": None})
        updated = JSONFieldModel.objects.update(
            data=Case(
                When(
                    data__key=Value(None, JSONField()),
                    then=Value({"key": "something"}, JSONField()),
                ),
            )
        )
        self.assertEqual(updated, 1)
        obj.refresh_from_db()
        self.assertEqual(obj.data, {"key": "something"})