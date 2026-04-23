def check_nested_input(
            input_props: dict[str, Any],
            field_name: str,
            context: str,
            block_name: str,
            block_id: str,
        ) -> bool:
            parent, child = field_name.split(DICT_SPLIT, 1)
            parent_schema = input_props.get(parent)
            if not parent_schema:
                self.add_error(
                    f"{context}: Parent property '{parent}' does not "
                    f"exist in block '{block_name}' ({block_id}) input "
                    f"schema."
                )
                return False

            allows_additional = parent_schema.get("additionalProperties", False)
            # Only anyOf is checked here because Pydantic's JSON schema
            # emits optional/union fields via anyOf. allOf and oneOf are
            # not currently used by any block's dict-typed inputs, so
            # false positives from them are not a concern in practice.
            if not allows_additional and "anyOf" in parent_schema:
                for schema_option in parent_schema.get("anyOf", []):
                    if not isinstance(schema_option, dict):
                        continue
                    if schema_option.get("additionalProperties"):
                        allows_additional = True
                        break
                    items_schema = schema_option.get("items")
                    if isinstance(items_schema, dict) and items_schema.get(
                        "additionalProperties"
                    ):
                        allows_additional = True
                        break

            if not allows_additional:
                if not (
                    isinstance(parent_schema, dict)
                    and "properties" in parent_schema
                    and isinstance(parent_schema["properties"], dict)
                    and child in parent_schema["properties"]
                ):
                    available = (
                        list(parent_schema.get("properties", {}).keys())
                        if isinstance(parent_schema, dict)
                        else []
                    )
                    self.add_error(
                        f"{context}: Child property '{child}' does not "
                        f"exist in parent '{parent}' of block "
                        f"'{block_name}' ({block_id}) input schema. "
                        f"Available properties: {available}"
                    )
                    return False
            return True