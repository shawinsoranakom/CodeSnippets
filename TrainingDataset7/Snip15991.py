def changelist_view(self, request):
        return super().changelist_view(request, extra_context={"extra_var": "Hello!"})