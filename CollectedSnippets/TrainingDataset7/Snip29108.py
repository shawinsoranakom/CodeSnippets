def get_formset(self, request, obj=None, **kwargs):
                kwargs["exclude"] = ["opening_band"]
                return super().get_formset(request, obj, **kwargs)