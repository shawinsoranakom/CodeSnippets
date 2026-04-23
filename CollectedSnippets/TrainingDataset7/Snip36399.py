def test_html_safe_subclass(self):
        class BaseClass:
            def __html__(self):
                # defines __html__ on its own
                return "some html content"

            def __str__(self):
                return "some non html content"

        @html_safe
        class Subclass(BaseClass):
            def __str__(self):
                # overrides __str__ and is marked as html_safe
                return "some html safe content"

        subclass_obj = Subclass()
        self.assertEqual(str(subclass_obj), subclass_obj.__html__())