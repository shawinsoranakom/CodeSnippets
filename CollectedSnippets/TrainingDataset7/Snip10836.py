def replace_expressions(self, replacements):
        if (replacement := replacements.get(self)) is not None:
            return replacement
        field_name, *transforms = self.name.split(LOOKUP_SEP)
        # Avoid unnecessarily looking up replacements with field_name again as
        # in the vast majority of cases F instances won't be composed of any
        # lookups.
        if not transforms:
            return self
        if (
            replacement := replacements.get(F(field_name))
        ) is None or replacement._output_field_or_none is None:
            return self
        for transform in transforms:
            transform_class = replacement.get_transform(transform)
            if transform_class is None:
                return self
            replacement = transform_class(replacement)
        return replacement