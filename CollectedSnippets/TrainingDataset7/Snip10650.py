def validate_constraints(self, exclude=None):
        constraints = self.get_constraints()
        using = router.db_for_write(self.__class__, instance=self)

        errors = {}
        for model_class, model_constraints in constraints:
            for constraint in model_constraints:
                try:
                    constraint.validate(model_class, self, exclude=exclude, using=using)
                except ValidationError as e:
                    if (
                        getattr(e, "code", None) == "unique"
                        and len(constraint.fields) == 1
                    ):
                        errors.setdefault(constraint.fields[0], []).append(e)
                    else:
                        errors = e.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)