def create_model(
        self, name, foreign_keys=[], bases=(), abstract=False, proxy=False
    ):
        test_name = "related_models_app"
        assert not (abstract and proxy)
        meta_contents = {
            "abstract": abstract,
            "app_label": test_name,
            "apps": self.apps,
            "proxy": proxy,
        }
        meta = type("Meta", (), meta_contents)
        if not bases:
            bases = (models.Model,)
        body = {
            "Meta": meta,
            "__module__": "__fake__",
        }
        fname_base = fname = "%s_%%d" % name.lower()
        for i, fk in enumerate(foreign_keys, 1):
            fname = fname_base % i
            body[fname] = fk
        return type(name, bases, body)