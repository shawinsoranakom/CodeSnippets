def test_unaccent_with_conforming_strings_off(self):
        """SQL is valid when standard_conforming_strings is off."""
        with connection.cursor() as cursor:
            cursor.execute("SHOW standard_conforming_strings")
            disable_conforming_strings = cursor.fetchall()[0][0] == "on"
            if disable_conforming_strings:
                cursor.execute("SET standard_conforming_strings TO off")
            try:
                self.assertQuerySetEqual(
                    self.Model.objects.filter(field__unaccent__endswith="éÖ"),
                    ["àéÖ", "aeO"],
                    transform=lambda instance: instance.field,
                    ordered=False,
                )
            finally:
                if disable_conforming_strings:
                    cursor.execute("SET standard_conforming_strings TO on")