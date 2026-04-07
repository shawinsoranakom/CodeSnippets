def get_form(self, request, obj=None, **kwargs):
                kwargs["exclude"] = ["bio"]
                return super().get_form(request, obj, **kwargs)