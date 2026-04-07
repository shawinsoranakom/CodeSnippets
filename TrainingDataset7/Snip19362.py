def test_checks_called_on_the_default_database(self):
        class Model(models.Model):
            field = models.CharField(max_length=100)

        model = Model()
        with self._patch_check_field_on("default") as mock_check_field_default:
            with self._patch_check_field_on("other") as mock_check_field_other:
                model.check(databases={"default", "other"})
                self.assertTrue(mock_check_field_default.called)
                self.assertFalse(mock_check_field_other.called)