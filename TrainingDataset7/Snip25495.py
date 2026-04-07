def test_fix_default_value(self):
        class Model(models.Model):
            field_dt = models.TimeField(default=now())
            field_t = models.TimeField(default=now().time())
            # Timezone-aware time object (when USE_TZ=True).
            field_tz = models.TimeField(default=now().timetz())
            field_now = models.DateField(default=now)

        names = ["field_dt", "field_t", "field_tz", "field_now"]
        fields = [Model._meta.get_field(name) for name in names]
        errors = []
        for field in fields:
            errors.extend(field.check())

        self.assertEqual(
            errors,
            [
                DjangoWarning(
                    "Fixed default value provided.",
                    hint="It seems you set a fixed date / time / datetime "
                    "value as default for this field. This may not be "
                    "what you want. If you want to have the current date "
                    "as default, use `django.utils.timezone.now`",
                    obj=fields[0],
                    id="fields.W161",
                ),
                DjangoWarning(
                    "Fixed default value provided.",
                    hint="It seems you set a fixed date / time / datetime "
                    "value as default for this field. This may not be "
                    "what you want. If you want to have the current date "
                    "as default, use `django.utils.timezone.now`",
                    obj=fields[1],
                    id="fields.W161",
                ),
                DjangoWarning(
                    "Fixed default value provided.",
                    hint=(
                        "It seems you set a fixed date / time / datetime value as "
                        "default for this field. This may not be what you want. "
                        "If you want to have the current date as default, use "
                        "`django.utils.timezone.now`"
                    ),
                    obj=fields[2],
                    id="fields.W161",
                ),
                # field_now doesn't raise a warning.
            ],
        )