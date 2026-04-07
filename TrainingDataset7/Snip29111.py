def get_formset(self, request, obj=None, **kwargs):
                kwargs["widgets"] = {"opening_band": Select}
                return super().get_formset(request, obj, **kwargs)