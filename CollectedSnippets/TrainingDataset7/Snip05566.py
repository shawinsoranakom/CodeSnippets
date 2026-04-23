def _check_save_on_top(self, obj):
        """Check save_on_top is a boolean."""

        if not isinstance(obj.save_on_top, bool):
            return must_be("a boolean", option="save_on_top", obj=obj, id="admin.E102")
        else:
            return []