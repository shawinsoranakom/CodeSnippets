def response_post_save_add(self, request, obj):
        return HttpResponseRedirect(
            reverse("admin:admin_custom_urls_person_history", args=[obj.pk])
        )