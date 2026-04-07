def test_auto_now_and_auto_now_add_raise_error(self):
        class Model(models.Model):
            field0 = models.DateTimeField(auto_now=True, auto_now_add=True, default=now)
            field1 = models.DateTimeField(
                auto_now=True, auto_now_add=False, default=now
            )
            field2 = models.DateTimeField(
                auto_now=False, auto_now_add=True, default=now
            )
            field3 = models.DateTimeField(
                auto_now=True, auto_now_add=True, default=None
            )

        expected = []
        checks = []
        for i in range(4):
            field = Model._meta.get_field("field%d" % i)
            expected.append(
                Error(
                    "The options auto_now, auto_now_add, and default "
                    "are mutually exclusive. Only one of these options "
                    "may be present.",
                    obj=field,
                    id="fields.E160",
                )
            )
            checks.extend(field.check())
            self.assertEqual(checks, expected)