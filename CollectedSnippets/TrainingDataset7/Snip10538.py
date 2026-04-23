def render(self, apps):
        """Create a Model object from our current state into the given apps."""
        # First, make a Meta object
        meta_options = {**self.options}
        # Prune index_together from options as it's no longer an allowed meta
        # attribute.
        meta_options.pop("index_together", None)
        meta_contents = {"app_label": self.app_label, "apps": apps, **meta_options}
        meta = type("Meta", (), meta_contents)
        # Then, work out our bases
        try:
            bases = tuple(
                (apps.get_model(base) if isinstance(base, str) else base)
                for base in self.bases
                if base != typing.Generic
            )
        except LookupError:
            raise InvalidBasesError(
                "Cannot resolve one or more bases from %r" % (self.bases,)
            )
        # Clone fields for the body, add other bits.
        body = {name: field.clone() for name, field in self.fields.items()}
        body["Meta"] = meta
        body["__module__"] = "__fake__"

        # Restore managers
        body.update(self.construct_managers())
        # Then, make a Model object (apps.register_model is called in __new__)
        return type(self.name, bases, body)