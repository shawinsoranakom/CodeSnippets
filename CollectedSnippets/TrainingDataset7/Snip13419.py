def find_template_loader(self, loader):
        if isinstance(loader, (tuple, list)):
            loader, *args = loader
        else:
            args = []

        if isinstance(loader, str):
            loader_class = import_string(loader)
            return loader_class(self, *args)
        else:
            raise ImproperlyConfigured(
                "Invalid value in template loaders configuration: %r" % loader
            )