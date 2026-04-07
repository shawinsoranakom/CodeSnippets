def response_add(self, request, obj, post_url_continue=None):
        return super().response_add(
            request,
            obj,
            post_url_continue=reverse(
                "admin:admin_custom_urls_car_history", args=[obj.pk]
            ),
        )