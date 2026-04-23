def get_default_prefix(cls):
        opts = cls.model._meta
        return (
            opts.app_label
            + "-"
            + opts.model_name
            + "-"
            + cls.ct_field.name
            + "-"
            + cls.ct_fk_field.name
        )