def compress(self, data_list):
        if data_list:
            # Raise a validation error if time or date is empty
            # (possible if SplitDateTimeField has required=False).
            if data_list[0] in self.empty_values:
                raise ValidationError(
                    self.error_messages["invalid_date"], code="invalid_date"
                )
            if data_list[1] in self.empty_values:
                raise ValidationError(
                    self.error_messages["invalid_time"], code="invalid_time"
                )
            result = datetime.datetime.combine(*data_list)
            return from_current_timezone(result)
        return None