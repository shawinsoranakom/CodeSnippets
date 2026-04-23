def update(self, condition: dict, new_value: dict, index_name: str, knowledgebase_id: str) -> bool:
        if not self._check_table_exists_cached(index_name):
            return True

        # For doc_meta tables, don't force kb_id in condition
        if not index_name.startswith("ragflow_doc_meta_"):
            condition["kb_id"] = knowledgebase_id
        filters = get_filters(condition)
        set_values: list[str] = []
        for k, v in new_value.items():
            if k == "remove":
                if isinstance(v, str):
                    set_values.append(f"{v} = NULL")
                else:
                    assert isinstance(v, dict), f"Expected str or dict for 'remove', got {type(new_value[k])}."
                    for kk, vv in v.items():
                        assert kk in array_columns, f"Column '{kk}' is not an array column."
                        set_values.append(f"{kk} = array_remove({kk}, {get_value_str(vv)})")
            elif k == "add":
                assert isinstance(v, dict), f"Expected str or dict for 'add', got {type(new_value[k])}."
                for kk, vv in v.items():
                    assert kk in array_columns, f"Column '{kk}' is not an array column."
                    set_values.append(f"{kk} = array_append({kk}, {get_value_str(vv)})")
            elif k == "metadata":
                assert isinstance(v, dict), f"Expected dict for 'metadata', got {type(new_value[k])}"
                set_values.append(f"{k} = {get_value_str(v)}")
                if v and "doc_id" in condition:
                    group_id = v.get("_group_id")
                    title = v.get("_title")
                    if group_id:
                        set_values.append(f"group_id = {get_value_str(group_id)}")
                    if title:
                        set_values.append(f"docnm_kwd = {get_value_str(title)}")
            else:
                set_values.append(f"{k} = {get_value_str(v)}")

        if not set_values:
            return True

        update_sql = (
            f"UPDATE {index_name}"
            f" SET {', '.join(set_values)}"
            f" WHERE {' AND '.join(filters)}"
        )
        logger.debug("OBConnection.update sql: %s", update_sql)

        try:
            self.client.perform_raw_text_sql(update_sql)
            return True
        except Exception as e:
            logger.error(f"OBConnection.update error: {str(e)}")
        return False