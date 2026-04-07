def test_case_expression_with_jsonnull_then(self):
        obj = JSONModel.objects.create(value={"key": "value"})
        JSONModel.objects.filter(pk=obj.pk).update(
            value=Case(
                When(value={"key": "value"}, then=JSONNull()),
            )
        )
        obj.refresh_from_db()
        self.assertIsNone(obj.value)