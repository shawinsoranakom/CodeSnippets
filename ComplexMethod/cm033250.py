def map_column_name(col_name):
        if col_name.lower() == "count(star)":
            return "COUNT(*)"

        # First, try to extract AS alias from any expression (aggregate functions, json_extract_string, etc.)
        # Pattern: anything AS alias_name
        as_match = re.search(r'\s+AS\s+([^\s,)]+)', col_name, re.IGNORECASE)
        if as_match:
            alias = as_match.group(1).strip('"\'')

            # Use the alias for display name lookup
            if alias in field_map:
                display = field_map[alias]
                return re.sub(r"(/.*|（[^（）]+）)", "", display)
            # If alias not in field_map, try to match case-insensitively
            for field_key, display_value in field_map.items():
                if field_key.lower() == alias.lower():
                    return re.sub(r"(/.*|（[^（）]+）)", "", display_value)
            # Return alias as-is if no mapping found
            return alias

        # Try direct mapping first (for simple column names)
        if col_name in field_map:
            display = field_map[col_name]
            # Clean up any suffix patterns
            return re.sub(r"(/.*|（[^（）]+）)", "", display)

        # Try case-insensitive match for simple column names
        col_lower = col_name.lower()
        for field_key, display_value in field_map.items():
            if field_key.lower() == col_lower:
                return re.sub(r"(/.*|（[^（）]+）)", "", display_value)

        # For aggregate expressions or complex expressions without AS alias,
        # try to replace field names with display names
        result = col_name
        for field_name, display_name in field_map.items():
            # Replace field_name with display_name in the expression
            result = result.replace(field_name, display_name)

        # Clean up any suffix patterns
        result = re.sub(r"(/.*|（[^（）]+）)", "", result)
        return result