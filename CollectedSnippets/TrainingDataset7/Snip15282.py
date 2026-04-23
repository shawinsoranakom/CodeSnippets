def response_post_save_change(self, request, obj):
        return HttpResponseRedirect(
            reverse("admin:admin_custom_urls_person_delete", args=[obj.pk])
        )