def test_migrate_to_other_database(self):
        """Regression test for #16039: migrate with --database option."""
        cts = ContentType.objects.using("other").filter(app_label="multiple_database")

        count = cts.count()
        self.assertGreater(count, 0)

        cts.delete()
        management.call_command(
            "migrate", verbosity=0, interactive=False, database="other"
        )
        self.assertEqual(cts.count(), count)