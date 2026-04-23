def end_serialization(self):
        self.options.setdefault("allow_unicode", True)
        yaml.dump(self.objects, self.stream, Dumper=DjangoSafeDumper, **self.options)