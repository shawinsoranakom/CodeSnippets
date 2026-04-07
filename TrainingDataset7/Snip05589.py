def _check_formset(self, obj):
        """Check formset is a subclass of BaseModelFormSet."""

        if not _issubclass(obj.formset, BaseModelFormSet):
            return must_inherit_from(
                parent="BaseModelFormSet", option="formset", obj=obj, id="admin.E206"
            )
        else:
            return []