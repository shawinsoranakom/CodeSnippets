def test_set_permissions_fk_to_using_parameter(self):
        Permission.objects.using("other").delete()
        with self.assertNumQueries(4, using="other") as captured_queries:
            create_permissions(apps.get_app_config("auth"), verbosity=0, using="other")
        self.assertIn("INSERT INTO", captured_queries[-1]["sql"].upper())
        self.assertGreater(Permission.objects.using("other").count(), 0)