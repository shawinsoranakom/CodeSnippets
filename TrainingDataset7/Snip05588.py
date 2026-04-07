def _check_min_num(self, obj):
        """Check that min_num is an integer."""

        if obj.min_num is None:
            return []
        elif not isinstance(obj.min_num, int):
            return must_be("an integer", option="min_num", obj=obj, id="admin.E205")
        else:
            return []