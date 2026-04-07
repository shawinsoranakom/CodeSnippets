def test_access_class_property_if_getitem_is_defined_in_metaclass(self):
        """
        If the metaclass defines __getitem__, the template system should use
        it to resolve the dot notation.
        """

        class MealMeta(type):
            def __getitem__(cls, name):
                return getattr(cls, name) + " is yummy."

        class Meals(metaclass=MealMeta):
            lunch = "soup"
            do_not_call_in_templates = True

            # Make class type subscriptable.
            def __class_getitem__(cls, key):
                from types import GenericAlias

                return GenericAlias(cls, key)

        self.assertEqual(Meals.lunch, "soup")
        self.assertEqual(Meals["lunch"], "soup is yummy.")

        output = self.engine.render_to_string("template", {"meals": Meals})
        self.assertEqual(output, "soup is yummy.")