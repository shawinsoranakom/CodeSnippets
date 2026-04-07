def test_create_permissions_checks_contenttypes_created(self):
        """
        `post_migrate` handler ordering isn't guaranteed. Simulate a case
        where create_permissions() is called before create_contenttypes().
        """
        # Warm the manager cache.
        ContentType.objects.get_for_model(Group)
        # Apply a deletion as if e.g. a database 'flush' had been executed.
        ContentType.objects.filter(app_label="auth", model="group").delete()
        # This fails with a foreign key constraint without the fix.
        create_permissions(apps.get_app_config("auth"), interactive=False, verbosity=0)