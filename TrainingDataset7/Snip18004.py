def test_permission_with_proxy_content_type_created(self):
        """
        A proxy model's permissions use its own content type rather than the
        content type of the concrete model.
        """
        opts = UserProxy._meta
        codename = get_permission_codename("add", opts)
        self.assertTrue(
            Permission.objects.filter(
                content_type__model=opts.model_name,
                content_type__app_label=opts.app_label,
                codename=codename,
            ).exists()
        )