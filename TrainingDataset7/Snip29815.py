def test_name_auto_generation(self):
        index = self.index_class(fields=["field"])
        index.set_name_with_model(CharFieldModel)
        self.assertRegex(
            index.name, r"postgres_te_field_[0-9a-f]{6}_%s" % self.index_class.suffix
        )