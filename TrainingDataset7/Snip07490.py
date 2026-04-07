def __call__(self, parser, namespace, value, option_string=None):
        try:
            setattr(namespace, self.dest, int(value))
        except ValueError:
            setattr(namespace, self.dest, value)