def convert_to_cache(self, value, record, validate=True):
        # any format -> cache format {name: value} or None
        if not value:
            return None

        if isinstance(value, Property):
            value = value._values

        elif isinstance(value, dict):
            # avoid accidental side effects from shared mutable data
            value = copy.deepcopy(value)

        elif isinstance(value, str):
            value = json.loads(value)
            if not isinstance(value, dict):
                raise ValueError(f"Wrong property value {value!r}")

        elif isinstance(value, list):
            # Convert the list with all definitions into a simple dict
            # {name: value} to store the strict minimum on the child
            self._remove_display_name(value)
            value = self._list_to_dict(value)

        else:
            raise TypeError(f"Wrong property type {type(value)!r}")

        if validate:
            # Sanitize `_html` flagged properties
            for property_name, property_value in value.items():
                if property_name.endswith('_html'):
                    value[property_name] = html_sanitize(
                        property_value,
                        **self.HTML_SANITIZE_OPTIONS,
                    )

        return value