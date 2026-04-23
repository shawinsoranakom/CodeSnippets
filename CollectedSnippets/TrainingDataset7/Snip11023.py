def deconstruct(self):
        """
        Return enough information to recreate the field as a 4-tuple:

         * The name of the field on the model, if contribute_to_class() has
           been run.
         * The import path of the field, including the class, e.g.
           django.db.models.IntegerField. This should be the most portable
           version, so less specific may be better.
         * A list of positional arguments.
         * A dict of keyword arguments.

        Note that the positional or keyword arguments must contain values of
        the following types (including inner values of collection types):

         * None, bool, str, int, float, complex, set, frozenset, list, tuple,
           dict
         * UUID
         * datetime.datetime (naive), datetime.date
         * top-level classes, top-level functions - will be referenced by their
           full import path
         * Storage instances - these have their own deconstruct() method

        This is because the values here must be serialized into a text format
        (possibly new Python code, possibly JSON) and these are the only types
        with encoding handlers defined.

        There's no need to return the exact way the field was instantiated this
        time, just ensure that the resulting field is the same - prefer keyword
        arguments over positional ones, and omit parameters with their default
        values.
        """
        # Work out path - we shorten it for known Django core fields
        path = f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        if path.startswith("django.db.models.fields."):
            submodule, _, remainder = path.removeprefix(
                "django.db.models.fields."
            ).partition(".")
            if submodule in (
                "related",
                "files",
                "generated",
                "json",
                "proxy",
                "composite",
            ):
                path = f"django.db.models.{remainder}"
            else:
                path = "django.db.models" + path.removeprefix("django.db.models.fields")

        # Build keywords dict of non-default values
        keywords = {}
        if (value := self._verbose_name) is not None:
            keywords["verbose_name"] = value
        if (value := self.primary_key) is not False:
            keywords["primary_key"] = value
        if (value := self.max_length) is not None:
            keywords["max_length"] = value
        if (value := self._unique) is not False:
            keywords["unique"] = value
        if (value := self.blank) is not False:
            keywords["blank"] = value
        if (value := self.null) is not False:
            keywords["null"] = value
        if (value := self.db_index) is not False:
            keywords["db_index"] = value
        if (value := self.default) is not NOT_PROVIDED:
            keywords["default"] = value
        if (value := self.db_default) is not NOT_PROVIDED:
            keywords["db_default"] = value
        if (value := self.editable) is not True:
            keywords["editable"] = value
        if (value := self.serialize) is not True:
            keywords["serialize"] = value
        if (value := self.unique_for_date) is not None:
            keywords["unique_for_date"] = value
        if (value := self.unique_for_month) is not None:
            keywords["unique_for_month"] = value
        if (value := self.unique_for_year) is not None:
            keywords["unique_for_year"] = value
        if (value := self.choices) is not None:
            if isinstance(value, CallableChoiceIterator):
                value = value.func
            keywords["choices"] = value
        if (value := self.help_text) != "":
            keywords["help_text"] = value
        if (value := self.db_column) is not None:
            keywords["db_column"] = value
        if (value := self.db_comment) is not None:
            keywords["db_comment"] = value
        if (value := self._db_tablespace) is not None:
            keywords["db_tablespace"] = value
        if (value := self.auto_created) is not False:
            keywords["auto_created"] = value
        if (value := self._validators) != []:
            keywords["validators"] = value
        if (value := self._error_messages) is not None:
            keywords["error_messages"] = value

        return (self.name, path, [], keywords)