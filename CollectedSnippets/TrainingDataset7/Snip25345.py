def test_multigeneration_inheritance(self):
        class GrandParent(models.Model):
            clash = models.IntegerField()

        class Parent(GrandParent):
            pass

        class Child(Parent):
            pass

        class GrandChild(Child):
            clash = models.IntegerField()

        self.assertEqual(
            GrandChild.check(),
            [
                Error(
                    "The field 'clash' clashes with the field 'clash' "
                    "from model 'invalid_models_tests.grandparent'.",
                    obj=GrandChild._meta.get_field("clash"),
                    id="models.E006",
                )
            ],
        )