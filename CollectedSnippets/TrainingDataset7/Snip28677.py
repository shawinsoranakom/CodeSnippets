def test_abstract_model_with_regular_python_mixin_mro(self):
        class AbstractModel(models.Model):
            name = models.CharField(max_length=255)
            age = models.IntegerField()

            class Meta:
                abstract = True

        class Mixin:
            age = None

        class Mixin2:
            age = 2

        class DescendantMixin(Mixin):
            pass

        class ConcreteModel(models.Model):
            foo = models.IntegerField()

        class ConcreteModel2(ConcreteModel):
            age = models.SmallIntegerField()

        def fields(model):
            if not hasattr(model, "_meta"):
                return []
            return [(f.name, f.__class__) for f in model._meta.get_fields()]

        model_dict = {"__module__": "model_inheritance"}
        model1 = type("Model1", (AbstractModel, Mixin), model_dict.copy())
        model2 = type("Model2", (Mixin2, AbstractModel), model_dict.copy())
        model3 = type("Model3", (DescendantMixin, AbstractModel), model_dict.copy())
        model4 = type("Model4", (Mixin2, Mixin, AbstractModel), model_dict.copy())
        model5 = type(
            "Model5", (Mixin2, ConcreteModel2, Mixin, AbstractModel), model_dict.copy()
        )

        self.assertEqual(
            fields(model1),
            [
                ("id", models.BigAutoField),
                ("name", models.CharField),
                ("age", models.IntegerField),
            ],
        )

        self.assertEqual(
            fields(model2), [("id", models.BigAutoField), ("name", models.CharField)]
        )
        self.assertEqual(getattr(model2, "age"), 2)

        self.assertEqual(
            fields(model3), [("id", models.BigAutoField), ("name", models.CharField)]
        )

        self.assertEqual(
            fields(model4), [("id", models.BigAutoField), ("name", models.CharField)]
        )
        self.assertEqual(getattr(model4, "age"), 2)

        self.assertEqual(
            fields(model5),
            [
                ("id", models.BigAutoField),
                ("foo", models.IntegerField),
                ("concretemodel_ptr", models.OneToOneField),
                ("age", models.SmallIntegerField),
                ("concretemodel2_ptr", models.OneToOneField),
                ("name", models.CharField),
            ],
        )