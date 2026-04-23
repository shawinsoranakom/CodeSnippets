def to_dict(self) -> dict:
        schema: dict = {
            "type": self.type.value if self.type else None,
            "description": self.description,
        }
        if self.type == "array":
            if self.items:
                schema["items"] = self.items.to_dict()
            schema["minItems"] = self.minItems
            schema["maxItems"] = self.maxItems
        elif self.type == "object":
            if self.properties:
                schema["properties"] = {
                    name: prop.to_dict() for name, prop in self.properties.items()
                }
                schema["required"] = [
                    name for name, prop in self.properties.items() if prop.required
                ]
        elif self.enum:
            schema["enum"] = self.enum
        else:
            schema["minumum"] = self.minimum
            schema["maximum"] = self.maximum

        schema = {k: v for k, v in schema.items() if v is not None}

        return schema