def test_implicit_inheritance(self):
        class CustomManager(models.Manager):
            pass

        class AbstractModel(models.Model):
            custom_manager = CustomManager()

            class Meta:
                abstract = True

        class PlainModel(models.Model):
            custom_manager = CustomManager()

        self.assertIsInstance(PlainModel._base_manager, models.Manager)
        self.assertIsInstance(PlainModel._default_manager, CustomManager)

        class ModelWithAbstractParent(AbstractModel):
            pass

        self.assertIsInstance(ModelWithAbstractParent._base_manager, models.Manager)
        self.assertIsInstance(ModelWithAbstractParent._default_manager, CustomManager)

        class ProxyModel(PlainModel):
            class Meta:
                proxy = True

        self.assertIsInstance(ProxyModel._base_manager, models.Manager)
        self.assertIsInstance(ProxyModel._default_manager, CustomManager)

        class MTIModel(PlainModel):
            pass

        self.assertIsInstance(MTIModel._base_manager, models.Manager)
        self.assertIsInstance(MTIModel._default_manager, CustomManager)