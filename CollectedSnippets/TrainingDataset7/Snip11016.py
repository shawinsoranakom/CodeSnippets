def _check_validators(self):
        errors = []
        for i, validator in enumerate(self.validators):
            if not callable(validator):
                errors.append(
                    checks.Error(
                        "All 'validators' must be callable.",
                        hint=(
                            "validators[{i}] ({repr}) isn't a function or "
                            "instance of a validator class.".format(
                                i=i,
                                repr=repr(validator),
                            )
                        ),
                        obj=self,
                        id="fields.E008",
                    )
                )
        return errors