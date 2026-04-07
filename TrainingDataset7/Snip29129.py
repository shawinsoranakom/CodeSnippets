def db_for_read(self, model, **hints):
        "Point all read operations on auth models to 'default'"
        if model._meta.app_label == "auth":
            # We use default here to ensure we can tell the difference
            # between a read request and a write request for Auth objects
            return "default"
        return None