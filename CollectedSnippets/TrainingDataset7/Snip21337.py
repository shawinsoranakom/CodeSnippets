def _test_slicing_of_f_expressions(self, model):
        tests = [
            (F("name")[:], "Example Inc."),
            (F("name")[:7], "Example"),
            (F("name")[:6][:5], "Examp"),  # Nested slicing.
            (F("name")[0], "E"),
            (F("name")[13], ""),
            (F("name")[8:], "Inc."),
            (F("name")[0:15], "Example Inc."),
            (F("name")[2:7], "ample"),
            (F("name")[1:][:3], "xam"),
            (F("name")[2:2], ""),
        ]
        for expression, expected in tests:
            with self.subTest(expression=expression, expected=expected):
                obj = model.objects.get(name="Example Inc.")
                try:
                    obj.name = expression
                    obj.save(update_fields=["name"])
                    obj.refresh_from_db()
                    self.assertEqual(obj.name, expected)
                finally:
                    obj.name = "Example Inc."
                    obj.save(update_fields=["name"])