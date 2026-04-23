def test_checks_are_performed(self):
        admin.site.register(Song, MyAdmin)
        try:
            errors = checks.run_checks()
            expected = ["error!"]
            self.assertEqual(errors, expected)
        finally:
            admin.site.unregister(Song)