def test_choices_named_group_lazy(self):
        class Model(models.Model):
            field = models.CharField(
                max_length=10,
                choices=[
                    [_("knights"), [["L", _("Lancelot")], ["G", _("Galahad")]]],
                    ["R", _("Random character")],
                ],
            )

        self.assertEqual(Model._meta.get_field("field").check(), [])