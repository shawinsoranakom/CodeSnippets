def allowed_host(cls):
        return cls.external_host or cls.host