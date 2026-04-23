def test_apps_bulk_update(self):
        """
        StateApps.bulk_update() should update apps.ready to False and reset
        the value afterward.
        """
        project_state = ProjectState()
        apps = project_state.apps
        with apps.bulk_update():
            self.assertFalse(apps.ready)
        self.assertTrue(apps.ready)
        with self.assertRaises(ValueError):
            with apps.bulk_update():
                self.assertFalse(apps.ready)
                raise ValueError()
        self.assertTrue(apps.ready)