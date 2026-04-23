def fields(model):
            if not hasattr(model, "_meta"):
                return []
            return [(f.name, f.__class__) for f in model._meta.get_fields()]