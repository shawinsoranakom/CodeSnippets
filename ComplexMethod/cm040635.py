def track(self, attr):
        if not is_tracking_enabled():
            return attr

        for store_name, (is_attr_type, _) in self.config.items():
            if is_attr_type(attr):
                if store_name in self.exclusions:
                    for excl in self.exclusions[store_name]:
                        if self.is_in_store(excl, attr):
                            return attr
                if not self.is_in_store(store_name, attr):
                    self.add_to_store(store_name, attr)
                return attr
        if isinstance(attr, tuple) and hasattr(attr, "_fields"):
            # Named tuple case.
            wrapped_attr = {}
            for name, e in attr._asdict().items():
                wrapped_attr[name] = self.track(e)
            return attr.__class__(**wrapped_attr)
        if isinstance(attr, tuple):
            wrapped_attr = []
            for e in attr:
                wrapped_attr.append(self.track(e))
            return attr.__class__(wrapped_attr)
        elif isinstance(attr, list):
            return TrackedList(attr, self)
        elif isinstance(attr, OrderedDict):
            return TrackedOrderedDict(attr, self)
        elif isinstance(attr, dict):
            return TrackedDict(attr, self)
        elif isinstance(attr, set):
            return TrackedSet(attr, self)
        return attr