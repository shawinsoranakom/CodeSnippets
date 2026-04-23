def test_subscriptable_class(self):
        class MyClass(list):
            # As of Python 3.9 list defines __class_getitem__ which makes it
            # subscriptable.
            class_property = "Example property"
            do_not_call_in_templates = True

            @classmethod
            def class_method(cls):
                return "Example method"

        for case in (MyClass, lambda: MyClass):
            with self.subTest(case=case):
                output = self.engine.render_to_string("template", {"class_var": case})
                self.assertEqual(output, "Example property | Example method")