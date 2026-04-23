def test_callable_uses_deferred_annotations(self):
        """
        Missing required arguments are gracefully handled when a signature uses
        deferred annotations.
        """

        class MyObject:
            @staticmethod
            def uses_deferred_annotations(value: AnnotatedKwarg):
                return value

        template = self._engine().from_string("{{ obj.uses_deferred_annotations }}")
        self.assertEqual(template.render(Context({"obj": MyObject()})), "")