def _parse_property_value(prop: dict) -> Any:
        """Parse a Notion property value into a simple Python type."""
        prop_type = prop.get("type")

        if prop_type == "title":
            return parse_rich_text(prop.get("title", []))
        elif prop_type == "rich_text":
            return parse_rich_text(prop.get("rich_text", []))
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "select":
            select = prop.get("select")
            return select.get("name") if select else None
        elif prop_type == "multi_select":
            return [item.get("name") for item in prop.get("multi_select", [])]
        elif prop_type == "date":
            date = prop.get("date")
            if date:
                return date.get("start")
            return None
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        elif prop_type == "url":
            return prop.get("url")
        elif prop_type == "email":
            return prop.get("email")
        elif prop_type == "phone_number":
            return prop.get("phone_number")
        elif prop_type == "people":
            return [
                person.get("name", person.get("id"))
                for person in prop.get("people", [])
            ]
        elif prop_type == "files":
            files = prop.get("files", [])
            return [
                f.get(
                    "name",
                    f.get("external", {}).get("url", f.get("file", {}).get("url")),
                )
                for f in files
            ]
        elif prop_type == "relation":
            return [rel.get("id") for rel in prop.get("relation", [])]
        elif prop_type == "formula":
            formula = prop.get("formula", {})
            return formula.get(formula.get("type"))
        elif prop_type == "rollup":
            rollup = prop.get("rollup", {})
            return rollup.get(rollup.get("type"))
        elif prop_type == "created_time":
            return prop.get("created_time")
        elif prop_type == "created_by":
            return prop.get("created_by", {}).get(
                "name", prop.get("created_by", {}).get("id")
            )
        elif prop_type == "last_edited_time":
            return prop.get("last_edited_time")
        elif prop_type == "last_edited_by":
            return prop.get("last_edited_by", {}).get(
                "name", prop.get("last_edited_by", {}).get("id")
            )
        else:
            # Return the raw value for unknown types
            return prop