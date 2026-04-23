def to_dict(
        self,
    ) -> dict[
        str,
        int | float | str | list[int] | list[float] | list[str],
    ]:
        """Convert the encoded attributes back to a dictionary for creating an ONNX node."""
        attrs: dict[
            str,
            int | float | str | list[int] | list[float] | list[str],
        ] = {}
        for i, key in enumerate(self.attr_keys):
            attr_type = self.attr_types[i]
            if attr_type == _INT_TYPE:
                attrs[key] = self.attr_ints[self.attr_pos[i][0]]
            elif attr_type == _FLOAT_TYPE:
                attrs[key] = self.attr_floats[self.attr_pos[i][0]]
            elif attr_type == _STRING_TYPE:
                attrs[key] = self.attr_strs[self.attr_pos[i][0]]
            elif attr_type == _FLOAT_SEQ_TYPE:
                attrs[key] = self.attr_floats[self.attr_pos[i][0] : self.attr_pos[i][1]]
            elif attr_type == _INT_SEQ_TYPE:
                attrs[key] = self.attr_ints[self.attr_pos[i][0] : self.attr_pos[i][1]]
            elif attr_type == _STRING_SEQ_TYPE:
                attrs[key] = self.attr_strs[self.attr_pos[i][0] : self.attr_pos[i][1]]
            else:
                raise ValueError(f"Unsupported attribute type: {attr_type}")
        return attrs