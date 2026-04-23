def test_model_check_method_not_shadowed(self, apps):
        class ModelWithAttributeCalledCheck(models.Model):
            check = 42

        class ModelWithFieldCalledCheck(models.Model):
            check = models.IntegerField()

        class ModelWithRelatedManagerCalledCheck(models.Model):
            pass

        class ModelWithDescriptorCalledCheck(models.Model):
            check = models.ForeignKey(
                ModelWithRelatedManagerCalledCheck, models.CASCADE
            )
            article = models.ForeignKey(
                ModelWithRelatedManagerCalledCheck,
                models.CASCADE,
                related_name="check",
            )

        errors = checks.run_checks(app_configs=apps.get_app_configs())
        expected = [
            Error(
                "The 'ModelWithAttributeCalledCheck.check()' class method is "
                "currently overridden by 42.",
                obj=ModelWithAttributeCalledCheck,
                id="models.E020",
            ),
            Error(
                "The 'ModelWithFieldCalledCheck.check()' class method is "
                "currently overridden by %r." % ModelWithFieldCalledCheck.check,
                obj=ModelWithFieldCalledCheck,
                id="models.E020",
            ),
            Error(
                "The 'ModelWithRelatedManagerCalledCheck.check()' class method is "
                "currently overridden by %r."
                % ModelWithRelatedManagerCalledCheck.check,
                obj=ModelWithRelatedManagerCalledCheck,
                id="models.E020",
            ),
            Error(
                "The 'ModelWithDescriptorCalledCheck.check()' class method is "
                "currently overridden by %r." % ModelWithDescriptorCalledCheck.check,
                obj=ModelWithDescriptorCalledCheck,
                id="models.E020",
            ),
        ]
        self.assertEqual(errors, expected)