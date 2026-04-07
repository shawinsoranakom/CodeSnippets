def _check_model_name_db_lookup_clashes(cls):
        errors = []
        model_name = cls.__name__
        if model_name.startswith("_") or model_name.endswith("_"):
            errors.append(
                checks.Error(
                    "The model name '%s' cannot start or end with an underscore "
                    "as it collides with the query lookup syntax." % model_name,
                    obj=cls,
                    id="models.E023",
                )
            )
        elif LOOKUP_SEP in model_name:
            errors.append(
                checks.Error(
                    "The model name '%s' cannot contain double underscores as "
                    "it collides with the query lookup syntax." % model_name,
                    obj=cls,
                    id="models.E024",
                )
            )
        return errors