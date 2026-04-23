def get_formsets_with_inlines(self, request, obj=None):
        if request.is_add_view and obj is not None:
            raise Exception(
                "'obj' passed to get_formsets_with_inlines wasn't None during add_view"
            )
        if not request.is_add_view and obj is None:
            raise Exception(
                "'obj' passed to get_formsets_with_inlines was None during change_view"
            )
        return super().get_formsets_with_inlines(request, obj)