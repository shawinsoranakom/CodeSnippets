def typescript_type(self) -> str:
        if not self.type:
            return "any"
        if self.type == JSONSchema.Type.BOOLEAN:
            return "boolean"
        if self.type in {JSONSchema.Type.INTEGER, JSONSchema.Type.NUMBER}:
            return "number"
        if self.type == JSONSchema.Type.STRING:
            return "string"
        if self.type == JSONSchema.Type.ARRAY:
            return f"Array<{self.items.typescript_type}>" if self.items else "Array"
        if self.type == JSONSchema.Type.OBJECT:
            if not self.properties:
                return "Record<string, any>"
            return self.to_typescript_object_interface()
        if self.enum:
            return " | ".join(repr(v) for v in self.enum)

        raise NotImplementedError(
            f"JSONSchema.typescript_type does not support Type.{self.type.name} yet"
        )