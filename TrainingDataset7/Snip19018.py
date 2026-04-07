def test_update_conflicts_unsupported(self):
        msg = "This database backend does not support updating conflicts."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Country.objects.bulk_create(self.data, update_conflicts=True)