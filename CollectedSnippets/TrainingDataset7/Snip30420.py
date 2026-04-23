def test_option_sql_injection(self):
        qs = Tag.objects.filter(name="test")
        options = {"SUMMARY true) SELECT 1; --": True}
        msg = "Invalid option name: 'SUMMARY true) SELECT 1; --'"
        with self.assertRaisesMessage(ValueError, msg):
            qs.explain(**options)