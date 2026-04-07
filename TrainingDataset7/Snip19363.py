def test_checks_called_on_the_other_database(self):
        class OtherModel(models.Model):
            field = models.CharField(max_length=100)

        model = OtherModel()
        with self._patch_check_field_on("other") as mock_check_field_other:
            with self._patch_check_field_on("default") as mock_check_field_default:
                model.check(databases={"default", "other"})
                self.assertTrue(mock_check_field_other.called)
                self.assertFalse(mock_check_field_default.called)