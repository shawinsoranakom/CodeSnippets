def test_objects_attribute_is_only_available_on_the_class_itself(self):
        with self.assertRaisesMessage(
            AttributeError, "Manager isn't accessible via Article instances"
        ):
            getattr(
                Article(),
                "objects",
            )
        self.assertFalse(hasattr(Article(), "objects"))
        self.assertTrue(hasattr(Article, "objects"))