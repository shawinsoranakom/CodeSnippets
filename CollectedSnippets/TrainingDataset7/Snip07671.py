def validate(self, value, model_instance):
        super().validate(value, model_instance)
        for index, part in enumerate(value):
            try:
                self.base_field.validate(part, model_instance)
            except exceptions.ValidationError as error:
                raise prefix_validation_error(
                    error,
                    prefix=self.error_messages["item_invalid"],
                    code="item_invalid",
                    params={"nth": index + 1},
                )
        if isinstance(self.base_field, ArrayField):
            if len({len(i) for i in value}) > 1:
                raise exceptions.ValidationError(
                    self.error_messages["nested_array_mismatch"],
                    code="nested_array_mismatch",
                )