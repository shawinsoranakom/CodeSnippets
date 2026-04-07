def test_load_working_egg(self):
        ttext = "{% load working_egg %}"
        egg_name = "%s/tagsegg.egg" % self.egg_dir
        with extend_sys_path(egg_name):
            engine = Engine(
                libraries={
                    "working_egg": "tagsegg.templatetags.working_egg",
                }
            )
            engine.from_string(ttext)