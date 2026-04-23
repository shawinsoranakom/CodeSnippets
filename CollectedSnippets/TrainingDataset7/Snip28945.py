def test_valid_field_accessible_via_instance(self):
        class PositionField(Field):
            """Custom field accessible only via instance."""

            def contribute_to_class(self, cls, name):
                super().contribute_to_class(cls, name)
                setattr(cls, self.name, self)

            def __get__(self, instance, owner):
                if instance is None:
                    raise AttributeError()

        class TestModel(Model):
            field = PositionField()

        class TestModelAdmin(ModelAdmin):
            list_display = ("field",)

        self.assertIsValid(TestModelAdmin, TestModel)