def test_display_decorator_with_boolean_and_empty_value(self):
        msg = (
            "The boolean and empty_value arguments to the @display decorator "
            "are mutually exclusive."
        )
        with self.assertRaisesMessage(ValueError, msg):

            class BookAdmin(admin.ModelAdmin):
                @admin.display(boolean=True, empty_value="(Missing)")
                def is_published(self, obj):
                    return obj.publish_date is not None