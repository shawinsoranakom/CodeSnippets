def _get_validated_value(self, name, attribute, value, templar):
        if attribute.isa == 'string':
            value = to_text(value)
        elif attribute.isa == 'int':
            if not isinstance(value, int):
                try:
                    if (decimal_value := decimal.Decimal(value)) != (int_value := int(decimal_value)):
                        raise decimal.DecimalException(f'Floating-point value {value!r} would be truncated.')
                    value = int_value
                except decimal.DecimalException as e:
                    raise ValueError from e
        elif attribute.isa == 'float':
            value = float(value)
        elif attribute.isa == 'bool':
            value = boolean(value, strict=True)
        elif attribute.isa == 'percent':
            # special value, which may be an integer or float
            # with an optional '%' at the end
            if isinstance(value, str) and '%' in value:
                value = value.replace('%', '')
            value = float(value)
        elif attribute.isa == 'list':
            if value is None:
                value = []
            elif not isinstance(value, list):
                value = [value]
            if attribute.listof is not None:
                for item in value:
                    if not isinstance(item, attribute.listof):
                        type_names = ' or '.join(f'{native_type_name(attribute_type)!r}' for attribute_type in attribute.listof)

                        raise AnsibleParserError(
                            message=f"Keyword {name!r} items must be of type {type_names}, not {native_type_name(item)!r}.",
                            obj=Origin.first_tagged_on(item, value, self.get_ds()),
                        )
                    elif attribute.required and attribute.listof == (str,):
                        if item is None or item.strip() == "":
                            raise AnsibleParserError(
                                message=f"Keyword {name!r} is required, and cannot have empty values.",
                                obj=Origin.first_tagged_on(item, value, self.get_ds()),
                            )
        elif attribute.isa == 'dict':
            if value is None:
                value = dict()
            elif not isinstance(value, dict):
                raise AnsibleError(f"{value!r} is not a dictionary")
        elif attribute.isa == 'class':
            if not isinstance(value, attribute.class_type):
                raise TypeError("%s is not a valid %s (got a %s instead)" % (name, attribute.class_type, type(value)))
            value.post_validate(templar=templar)
        else:
            raise AnsibleAssertionError(f"Unknown value for attribute.isa: {attribute.isa}")
        return value