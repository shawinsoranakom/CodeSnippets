def _create_column(
        self, 
        name: str, 
        ob_type: str, 
        nullable: bool,
        default: Any,
        is_primary: bool,
        is_array: bool,
    ) -> Column:
        """Create a SQLAlchemy Column object based on type string."""

        # Handle array types
        if is_array or ob_type.startswith("ARRAY"):
            # Extract inner type
            if "String" in ob_type:
                inner_type = String(256)
            elif "Integer" in ob_type:
                inner_type = Integer
            else:
                inner_type = String(256)

            # Nested array (e.g., ARRAY(ARRAY(Integer)))
            if ob_type.count("ARRAY") > 1:
                return Column(name, ARRAY(ARRAY(inner_type)), nullable=nullable)
            else:
                return Column(name, ARRAY(inner_type), nullable=nullable)

        # Handle String types with length
        if ob_type.startswith("String"):
            # Extract length: String(256) -> 256
            import re
            match = re.search(r'\((\d+)\)', ob_type)
            length = int(match.group(1)) if match else 256
            return Column(
                name, String(length), 
                primary_key=is_primary, 
                nullable=nullable,
                server_default=f"'{default}'" if default else None
            )

        # Map other types
        type_map = {
            "Integer": Integer,
            "Double": Double,
            "Float": Float,
            "JSON": JSON,
            "LONGTEXT": LONGTEXT,
            "TEXT": MYSQL_TEXT,
        }

        for type_name, type_class in type_map.items():
            if type_name in ob_type:
                return Column(
                    name, type_class, 
                    primary_key=is_primary,
                    nullable=nullable,
                    server_default=str(default) if default is not None else None
                )

        # Default to String
        return Column(name, String(256), nullable=nullable)