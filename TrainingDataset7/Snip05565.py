def _check_save_as(self, obj):
        """Check save_as is a boolean."""

        if not isinstance(obj.save_as, bool):
            return must_be("a boolean", option="save_as", obj=obj, id="admin.E101")
        else:
            return []