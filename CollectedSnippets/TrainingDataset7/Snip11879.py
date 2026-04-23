def many_to_many(self):
        """
        Return a list of all many to many fields on the model and its parents.

        Private API intended only to be used by Django itself; get_fields()
        combined with filtering of field properties is the public API for
        obtaining this list.
        """
        return make_immutable_fields_list(
            "many_to_many",
            (
                f
                for f in self._get_fields(reverse=False)
                if f.is_relation and f.many_to_many
            ),
        )