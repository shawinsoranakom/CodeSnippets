def get_dirs(self):
        for loader in self.loaders:
            if hasattr(loader, "get_dirs"):
                yield from loader.get_dirs()