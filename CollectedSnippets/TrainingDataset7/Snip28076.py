def test_key_sql_injection_escape(self):
        query = str(
            JSONModel.objects.filter(
                **{
                    """value__test") = '"a"' OR 1 = 1 OR ("d""": "x",
                }
            ).query
        )
        self.assertIn('"test\\"', query)
        self.assertIn('\\"d', query)