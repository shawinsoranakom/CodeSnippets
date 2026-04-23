def test_abstract_model_with_custom_manager_name(self):
        """
        A custom manager may be defined on an abstract model.
        It will be inherited by the abstract model's children.
        """
        PersonFromAbstract.abstract_persons.create(objects="Test")
        self.assertQuerySetEqual(
            PersonFromAbstract.abstract_persons.all(),
            ["Test"],
            lambda c: c.objects,
        )