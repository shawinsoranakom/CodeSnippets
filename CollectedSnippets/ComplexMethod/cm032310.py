def update(self, condition: dict, new_value: dict, index_name: str, memory_id: str) -> bool:
        """Update messages with given condition."""
        if not self._check_table_exists_cached(index_name):
            return True

        condition["memory_id"] = memory_id
        condition_dict = {self.convert_field_name(k): v for k, v in condition.items()}
        filters = self._get_filters(condition_dict)

        update_dict = {self.convert_field_name(k): v for k, v in new_value.items()}
        if "content_ltks" in update_dict:
            update_dict["tokenized_content_ltks"] = fine_grained_tokenize(tokenize(update_dict["content_ltks"]))
        update_dict.pop("id", None)

        set_values: list[str] = []
        for k, v in update_dict.items():
            if k == "remove":
                if isinstance(v, str):
                    set_values.append(f"{v} = NULL")
            elif k == "status":
                set_values.append(f"status_int = {1 if v else 0}")
            else:
                set_values.append(f"{k} = {get_value_str(v)}")

        if not set_values:
            return True

        update_sql = (
            f"UPDATE {index_name}"
            f" SET {', '.join(set_values)}"
            f" WHERE {' AND '.join(filters)}"
        )
        self.logger.debug("OBConnection.update sql: %s", update_sql)

        try:
            self.client.perform_raw_text_sql(update_sql)
            return True
        except Exception as e:
            self.logger.error(f"OBConnection.update error: {str(e)}")
        return False