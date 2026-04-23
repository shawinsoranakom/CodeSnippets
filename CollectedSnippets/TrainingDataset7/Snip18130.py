def test_load_data_with_user_permissions(self):
        # Create test contenttypes for both databases
        default_objects = [
            ContentType.objects.db_manager("default").create(
                model="examplemodela",
                app_label="app_a",
            ),
            ContentType.objects.db_manager("default").create(
                model="examplemodelb",
                app_label="app_b",
            ),
        ]
        other_objects = [
            ContentType.objects.db_manager("other").create(
                model="examplemodelb",
                app_label="app_b",
            ),
            ContentType.objects.db_manager("other").create(
                model="examplemodela",
                app_label="app_a",
            ),
        ]

        # Now we create the test UserPermission
        Permission.objects.db_manager("default").create(
            name="Can delete example model b",
            codename="delete_examplemodelb",
            content_type=default_objects[1],
        )
        Permission.objects.db_manager("other").create(
            name="Can delete example model b",
            codename="delete_examplemodelb",
            content_type=other_objects[0],
        )

        perm_default = Permission.objects.get_by_natural_key(
            "delete_examplemodelb",
            "app_b",
            "examplemodelb",
        )

        perm_other = Permission.objects.db_manager("other").get_by_natural_key(
            "delete_examplemodelb",
            "app_b",
            "examplemodelb",
        )

        self.assertEqual(perm_default.content_type_id, default_objects[1].id)
        self.assertEqual(perm_other.content_type_id, other_objects[0].id)