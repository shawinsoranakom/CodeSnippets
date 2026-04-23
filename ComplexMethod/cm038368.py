def repair_param_type(self, param_type: str) -> str:
        """Repair unknown parameter types by treating them as string
        Args:
            param_type: Parameter type

        Returns:
            Repaired parameter type
        """
        if (
            param_type in ["string", "str", "text", "varchar", "char", "enum"]
            or param_type.startswith("int")
            or param_type.startswith("uint")
            or param_type.startswith("long")
            or param_type.startswith("short")
            or param_type.startswith("unsigned")
            or param_type.startswith("num")
            or param_type.startswith("float")
            or param_type in ["boolean", "bool", "binary"]
            or (
                param_type in ["object", "array", "arr", "sequence"]
                or param_type.startswith("dict")
                or param_type.startswith("list")
            )
        ):
            return param_type
        else:
            return "string"