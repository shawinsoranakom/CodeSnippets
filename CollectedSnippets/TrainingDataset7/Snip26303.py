def test_base_manager_inheritance(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            another_manager = models.Manager()
            custom_manager = CustomManager()

            class Meta:
                base_manager_name = "custom_manager"
                abstract = True

        class PlainModel(models.Model):
            another_manager = models.Manager()
            custom_manager = CustomManager()

            class Meta:
                base_manager_name = "custom_manager"

        self.assertIsInstance(PlainModel._base_manager, CustomManager)

        class ModelWithAbstractParent(AbstractModel):
            pass

        self.assertIsInstance(ModelWithAbstractParent._base_manager, CustomManager)

        class ProxyModel(PlainModel):
            class Meta:
                proxy = True

        self.assertIsInstance(ProxyModel._base_manager, CustomManager)

        class MTIModel(PlainModel):
            pass

        self.assertIsInstance(MTIModel._base_manager, CustomManager)