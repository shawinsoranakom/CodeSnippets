def test_ignore_update_conflicts_exclusive(self):
        msg = "ignore_conflicts and update_conflicts are mutually exclusive"
        with self.assertRaisesMessage(ValueError, msg):
            Country.objects.bulk_create(
                self.data,
                ignore_conflicts=True,
                update_conflicts=True,
            )