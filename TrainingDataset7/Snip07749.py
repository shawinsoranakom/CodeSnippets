def clean(self, value):
        cleaned_data = []
        errors = []
        if not any(value) and self.required:
            raise ValidationError(self.error_messages["required"])
        max_size = max(self.size, len(value))
        for index in range(max_size):
            item = value[index]
            try:
                cleaned_data.append(self.base_field.clean(item))
            except ValidationError as error:
                errors.append(
                    prefix_validation_error(
                        error,
                        self.error_messages["item_invalid"],
                        code="item_invalid",
                        params={"nth": index + 1},
                    )
                )
                cleaned_data.append(item)
            else:
                errors.append(None)
        cleaned_data, null_index = self._remove_trailing_nulls(cleaned_data)
        if null_index is not None:
            errors = errors[:null_index]
        errors = list(filter(None, errors))
        if errors:
            raise ValidationError(list(chain.from_iterable(errors)))
        return cleaned_data