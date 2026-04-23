def urlpatterns():
            return (
                path("admin/doc/", include("django.contrib.admindocs.urls")),
                path("admin/", admin.site.urls),
            )