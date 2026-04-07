def validate(self, value):
        super().validate(value)
        errors = []
        for index, item in enumerate(value):
            try:
                self.base_field.validate(item)
            except ValidationError as error:
                errors.append(
                    prefix_validation_error(
                        error,
                        prefix=self.error_messages["item_invalid"],
                        code="item_invalid",
                        params={"nth": index + 1},
                    )
                )
        if errors:
            raise ValidationError(errors)