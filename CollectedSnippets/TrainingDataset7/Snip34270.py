def test_load_error_egg(self):
        egg_name = "%s/tagsegg.egg" % self.egg_dir
        msg = (
            "Invalid template library specified. ImportError raised when "
            "trying to load 'tagsegg.templatetags.broken_egg': cannot "
            "import name 'Xtemplate'"
        )
        with extend_sys_path(egg_name):
            with self.assertRaisesMessage(InvalidTemplateLibrary, msg):
                Engine(libraries={"broken_egg": "tagsegg.templatetags.broken_egg"})