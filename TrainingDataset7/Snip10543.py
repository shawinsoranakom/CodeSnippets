def flatten_bases(model):
            bases = []
            for base in model.__bases__:
                if hasattr(base, "_meta") and base._meta.abstract:
                    bases.extend(flatten_bases(base))
                else:
                    bases.append(base)
            return bases