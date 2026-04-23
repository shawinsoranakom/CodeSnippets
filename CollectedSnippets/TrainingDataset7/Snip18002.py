def test_unavailable_models(self):
        """
        #24075 - Permissions shouldn't be created or deleted if the ContentType
        or Permission models aren't available.
        """
        state = migrations.state.ProjectState()
        # Unavailable contenttypes.ContentType
        with self.assertNumQueries(0):
            create_permissions(self.app_config, verbosity=0, apps=state.apps)
        # Unavailable auth.Permission
        state = migrations.state.ProjectState(real_apps={"contenttypes"})
        with self.assertNumQueries(0):
            create_permissions(self.app_config, verbosity=0, apps=state.apps)