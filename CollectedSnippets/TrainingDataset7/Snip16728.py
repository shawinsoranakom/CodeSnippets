def test_custom_admin_site(self):
        model_admin = ModelAdmin(City, customadmin.site)
        content_type_pk = ContentType.objects.get_for_model(City).pk
        redirect_url = model_admin.get_view_on_site_url(self.c1)
        self.assertEqual(
            redirect_url,
            reverse(
                f"{customadmin.site.name}:view_on_site",
                kwargs={
                    "content_type_id": content_type_pk,
                    "object_id": self.c1.pk,
                },
            ),
        )