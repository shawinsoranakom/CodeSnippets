def __call__(self, parser, namespace, value, option_string=None):
        if value.lower() == "true":
            setattr(namespace, self.dest, True)
        else:
            setattr(namespace, self.dest, value.split(","))