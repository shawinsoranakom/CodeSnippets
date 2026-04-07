def test_get_deleted_objects_with_custom_has_delete_permission(self):
        """
        ModelAdmin.get_deleted_objects() uses
        ModelAdmin.has_delete_permission() for permissions checking.
        """
        mock_request = MockRequest()
        mock_request.user = User.objects.create_superuser(
            username="bob", email="bob@test.com", password="test"
        )

        class TestModelAdmin(ModelAdmin):
            def has_delete_permission(self, request, obj=None):
                return False

        self.site.register(Band, TestModelAdmin)
        ma = self.site.get_model_admin(Band)
        (
            deletable_objects,
            model_count,
            perms_needed,
            protected,
        ) = ma.get_deleted_objects([self.band], request)
        self.assertEqual(deletable_objects, ["Band: The Doors"])
        self.assertEqual(model_count, {"bands": 1})
        self.assertEqual(perms_needed, {"band"})
        self.assertEqual(protected, [])