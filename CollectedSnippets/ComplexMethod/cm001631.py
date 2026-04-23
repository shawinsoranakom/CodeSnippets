def set(self, key, value, is_api=False, run_callbacks=True):
        """sets an option and calls its onchange callback, returning True if the option changed and False otherwise"""

        oldval = self.data.get(key, None)
        if oldval == value:
            return False

        option = self.data_labels[key]
        if option.do_not_save:
            return False

        if is_api and option.restrict_api:
            return False

        try:
            setattr(self, key, value)
        except RuntimeError:
            return False

        if run_callbacks and option.onchange is not None:
            try:
                option.onchange()
            except Exception as e:
                errors.display(e, f"changing setting {key} to {value}")
                setattr(self, key, oldval)
                return False

        return True