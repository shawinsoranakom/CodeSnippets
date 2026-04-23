def update_build_config(self, build_config, field_value, field_name=None):
        dynamic_fields = [
            "column_name",
            "filter_value",
            "filter_operator",
            "ascending",
            "new_column_name",
            "new_column_value",
            "columns_to_select",
            "num_rows",
            "replace_value",
            "replacement_value",
            "left_dataframe",
            "right_dataframe",
            "merge_on_column",
            "merge_how",
        ]
        for field in dynamic_fields:
            build_config[field]["show"] = False

        if field_name == "operation":
            # Handle SortableListInput format
            if isinstance(field_value, list):
                operation_name = field_value[0].get("name", "") if field_value else ""
            else:
                operation_name = field_value or ""

            # If no operation selected, all dynamic fields stay hidden (already set to False above)
            if not operation_name:
                return build_config

            if operation_name == "Filter":
                build_config["column_name"]["show"] = True
                build_config["filter_value"]["show"] = True
                build_config["filter_operator"]["show"] = True
            elif operation_name == "Sort":
                build_config["column_name"]["show"] = True
                build_config["ascending"]["show"] = True
            elif operation_name == "Drop Column":
                build_config["column_name"]["show"] = True
            elif operation_name == "Rename Column":
                build_config["column_name"]["show"] = True
                build_config["new_column_name"]["show"] = True
            elif operation_name == "Add Column":
                build_config["new_column_name"]["show"] = True
                build_config["new_column_value"]["show"] = True
            elif operation_name == "Select Columns":
                build_config["columns_to_select"]["show"] = True
            elif operation_name in {"Head", "Tail"}:
                build_config["num_rows"]["show"] = True
            elif operation_name == "Replace Value":
                build_config["column_name"]["show"] = True
                build_config["replace_value"]["show"] = True
                build_config["replacement_value"]["show"] = True
            elif operation_name == "Drop Duplicates":
                build_config["column_name"]["show"] = True
            elif operation_name == "Merge":
                build_config["left_dataframe"]["show"] = True
                build_config["right_dataframe"]["show"] = True
                build_config["merge_on_column"]["show"] = True
                build_config["merge_how"]["show"] = True

        return build_config