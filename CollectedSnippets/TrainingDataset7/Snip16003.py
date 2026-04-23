def delete_queryset(self, request, queryset):
        SubscriberAdmin.overridden = True
        super().delete_queryset(request, queryset)