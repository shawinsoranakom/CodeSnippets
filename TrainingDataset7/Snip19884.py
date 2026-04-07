def test_generic_foreign_key_checks_are_performed(self):
        class Model(models.Model):
            content_object = GenericForeignKey()

        with mock.patch.object(GenericForeignKey, "check") as check:
            checks.run_checks(app_configs=self.apps.get_app_configs())
        check.assert_called_once_with()