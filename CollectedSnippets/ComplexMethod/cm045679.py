def assert_matches_schema(
        self,
        other: type[Schema],
        *,
        allow_superset: bool = True,
        ignore_primary_keys: bool = True,
        allow_subtype: bool = True,
        ignore_properties: bool = True,
    ) -> None:
        self_dict = self._dtypes()
        other_dict = other._dtypes()

        # Check if self has all columns of other
        if self_dict.keys() < other_dict.keys():
            missing_columns = other_dict.keys() - self_dict.keys()
            raise AssertionError(f"schema does not have columns {missing_columns}")

        # Check if types of columns are the same
        for col in other_dict:
            assert other_dict[col] == self_dict[col] or (
                allow_subtype and dt.dtype_issubclass(self_dict[col], other_dict[col])
            ), (
                f"type of column {col} does not match - its type is {self_dict[col]} in {self.__name__}",
                f" and {other_dict[col]} in {other.__name__}",
            )

        # When allow_superset=False, check that self does not have extra columns
        if not allow_superset and self_dict.keys() > other_dict.keys():
            extra_columns = self_dict.keys() - other_dict.keys()
            raise AssertionError(
                f"there are extra columns: {extra_columns} which are not present in the provided schema"
            )

        # Check whether primary keys are the same
        if not ignore_primary_keys:
            assert self.primary_key_columns() == other.primary_key_columns(), (
                f"primary keys in the schemas do not match - they are {self.primary_key_columns()} in {self.__name__}",
                f" and {other.primary_key_columns()} in {other.__name__}",
            )
        if not ignore_properties:
            self_columns = self.columns()
            other_columns = other.columns()
            for column_name, column_schema in self_columns.items():
                other_column_schema = other_columns[column_name]
                assert column_schema == other_column_schema