def test_check_field(self):
        """Test if backend specific checks are performed."""
        error = Error("an error")

        class Model(models.Model):
            field = models.IntegerField()

        field = Model._meta.get_field("field")
        with mock.patch.object(
            connections["default"].validation, "check_field", return_value=[error]
        ):
            self.assertEqual(field.check(databases={"default"}), [error])