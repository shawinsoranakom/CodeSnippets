def get_inlines(self, request, obj):
        if obj is not None and obj.show_inlines:
            return [ShowInlineChildInline]
        return []