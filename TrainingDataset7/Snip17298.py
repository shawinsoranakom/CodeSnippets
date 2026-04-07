def test_model_clash(self):
        """
        Test for behavior when two models clash in the app registry.
        """
        new_apps = Apps(["apps"])
        meta_contents = {
            "app_label": "apps",
            "apps": new_apps,
        }

        body = {}
        body["Meta"] = type("Meta", (), meta_contents)
        body["__module__"] = TotallyNormal.__module__
        type("SouthPonies", (models.Model,), body)

        # When __name__ and __module__ match we assume the module
        # was reloaded and issue a warning. This use-case is
        # useful for REPL. Refs #23621.
        body = {}
        body["Meta"] = type("Meta", (), meta_contents)
        body["__module__"] = TotallyNormal.__module__
        msg = (
            "Model 'apps.southponies' was already registered. "
            "Reloading models is not advised as it can lead to inconsistencies, "
            "most notably with related models."
        )
        with self.assertRaisesMessage(RuntimeWarning, msg):
            type("SouthPonies", (models.Model,), body)

        # If it doesn't appear to be a reloaded module then we expect
        # a RuntimeError.
        body = {}
        body["Meta"] = type("Meta", (), meta_contents)
        body["__module__"] = TotallyNormal.__module__ + ".whatever"
        with self.assertRaisesMessage(
            RuntimeError, "Conflicting 'southponies' models in application 'apps':"
        ):
            type("SouthPonies", (models.Model,), body)