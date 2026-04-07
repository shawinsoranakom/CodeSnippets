def test_manager_no_duplicates(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            custom_manager = models.Manager()

            class Meta:
                abstract = True

        class TestModel(AbstractModel):
            custom_manager = CustomManager()

        self.assertEqual(TestModel._meta.managers, (TestModel.custom_manager,))
        self.assertEqual(
            TestModel._meta.managers_map, {"custom_manager": TestModel.custom_manager}
        )