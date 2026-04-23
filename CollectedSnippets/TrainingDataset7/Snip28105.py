def setUpTestData(cls):
        cls.msg = (
            "Using None as the right-hand side of an exact lookup on JSONField to mean "
            "JSON scalar 'null' is deprecated. Use JSONNull() instead (or use the "
            "__isnull lookup if you meant SQL NULL)."
        )
        cls.obj = NullableJSONModel.objects.create(value=JSONNull())