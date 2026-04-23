def test_empty_selection_hides_fields(self, component):
        """Test that all fields hide when operation is deselected."""
        build_config = {
            "column_name": {"show": True},
            "filter_value": {"show": True},
            "filter_operator": {"show": True},
            "ascending": {"show": True},
            "new_column_name": {"show": True},
            "new_column_value": {"show": True},
            "columns_to_select": {"show": True},
            "num_rows": {"show": True},
            "replace_value": {"show": True},
            "replacement_value": {"show": True},
            "merge_on_column": {"show": True},
            "merge_how": {"show": True},
            "left_dataframe": {"show": True},
            "right_dataframe": {"show": True},
        }

        # Deselect operation (empty list)
        updated_config = component.update_build_config(
            build_config,
            [],  # Empty selection
            "operation",
        )

        # All fields should be hidden
        assert updated_config["column_name"]["show"] is False
        assert updated_config["filter_value"]["show"] is False
        assert updated_config["filter_operator"]["show"] is False
        assert updated_config["ascending"]["show"] is False
        assert updated_config["new_column_name"]["show"] is False
        assert updated_config["new_column_value"]["show"] is False
        assert updated_config["columns_to_select"]["show"] is False
        assert updated_config["num_rows"]["show"] is False
        assert updated_config["replace_value"]["show"] is False
        assert updated_config["replacement_value"]["show"] is False
        assert updated_config["merge_on_column"]["show"] is False
        assert updated_config["merge_how"]["show"] is False
        assert updated_config["left_dataframe"]["show"] is False
        assert updated_config["right_dataframe"]["show"] is False