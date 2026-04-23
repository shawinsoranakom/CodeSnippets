def print_declaration(self, output, doc=True, quote_types=False):
        shape = self.shape

        q = '"' if quote_types else ""

        if isinstance(shape, StructureShape):
            self._print_structure_declaration(output, doc, quote_types)
        elif isinstance(shape, ListShape):
            output.write(
                f"{to_valid_python_name(shape.name)} = list[{q}{to_valid_python_name(shape.member.name)}{q}]"
            )
        elif isinstance(shape, MapShape):
            if is_sparse_shape(shape):
                value_key = f"{q}{to_valid_python_name(shape.value.name)} | None{q}"
            else:
                value_key = f"{q}{to_valid_python_name(shape.value.name)}{q}"
            output.write(
                f"{to_valid_python_name(shape.name)} = dict[{q}{to_valid_python_name(shape.key.name)}{q}, {value_key}]"
            )
        elif isinstance(shape, StringShape):
            if shape.enum:
                output.write(f"class {to_valid_python_name(shape.name)}(StrEnum):\n")
                for value in shape.enum:
                    name = to_valid_python_name(value)
                    output.write(f'    {name} = "{value}"\n')
            else:
                output.write(f"{to_valid_python_name(shape.name)} = str")
        elif shape.type_name == "string":
            output.write(f"{to_valid_python_name(shape.name)} = str")
        elif shape.type_name == "integer":
            output.write(f"{to_valid_python_name(shape.name)} = int")
        elif shape.type_name == "long":
            output.write(f"{to_valid_python_name(shape.name)} = int")
        elif shape.type_name == "double":
            output.write(f"{to_valid_python_name(shape.name)} = float")
        elif shape.type_name == "float":
            output.write(f"{to_valid_python_name(shape.name)} = float")
        elif shape.type_name == "boolean":
            output.write(f"{to_valid_python_name(shape.name)} = bool")
        elif shape.type_name == "blob":
            # blobs are often associated with streaming payloads, but we handle that on operation level,
            # not on shape level
            output.write(f"{to_valid_python_name(shape.name)} = bytes")
        elif shape.type_name == "timestamp":
            output.write(f"{to_valid_python_name(shape.name)} = datetime")
        else:
            output.write(
                f"# unknown shape type for {to_valid_python_name(shape.name)}: {shape.type_name}"
            )
        # TODO: BoxedInteger?

        output.write("\n")