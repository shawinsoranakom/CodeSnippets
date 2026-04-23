def test_egg5(self):
        """
        Loading an app from an egg that has an import error in its models
        module raises that error.
        """
        egg_name = "%s/brokenapp.egg" % self.egg_dir
        with extend_sys_path(egg_name):
            with self.assertRaisesMessage(ImportError, "modelz"):
                with self.settings(INSTALLED_APPS=["broken_app"]):
                    pass