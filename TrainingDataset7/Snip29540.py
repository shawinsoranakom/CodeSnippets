def test_hstore_field(self):
        class HStoreFieldModel(PostgreSQLModel):
            field = HStoreField()

        field = HStoreFieldModel._meta.get_field("field")
        self.assert_model_check_errors(
            HStoreFieldModel,
            [
                self._make_error(field, "HStoreField"),
            ],
        )