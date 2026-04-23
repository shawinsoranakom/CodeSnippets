def clean(self):
                try:
                    raise ValidationError({"code": [ValidationError("Code error 1.")]})
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError({"code": [ValidationError("Code error 2.")]})
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError({"code": ErrorList(["Code error 3."])})
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError("Non-field error 1.")
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                try:
                    raise ValidationError([ValidationError("Non-field error 2.")])
                except ValidationError as e:
                    self._errors = e.update_error_dict(self._errors)

                # The newly added list of errors is an instance of ErrorList.
                for field, error_list in self._errors.items():
                    if not isinstance(error_list, self.error_class):
                        self._errors[field] = self.error_class(error_list)