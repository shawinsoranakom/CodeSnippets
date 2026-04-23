def ask_not_null_alteration(self, field_name, model_name):
        # We can't ask the user, so set as not provided.
        self.log(
            f"Field '{field_name}' on model '{model_name}' given a default of "
            f"NOT PROVIDED and must be corrected."
        )
        return NOT_PROVIDED