def test_choices_containing_lazy(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=10, choices=[["1", _("1")], ["2", _("2")]]
            )

        self.assertEqual(Model._meta.get_field("field").check(), [])