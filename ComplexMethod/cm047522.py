def get(key, get_context=self.context.get):
            if key == 'company':
                return self.company.id
            elif key == 'uid':
                return self.uid if field.compute_sudo else (self.uid, self.su)
            elif key == 'lang':
                return get_context('lang') or None
            elif key == 'active_test':
                return get_context('active_test', field.context.get('active_test', True))
            elif key.startswith('bin_size'):
                return bool(get_context(key))
            else:
                val = get_context(key)
                if type(val) is list:
                    val = tuple(val)
                try:
                    hash(val)
                except TypeError:
                    raise TypeError(
                        "Can only create cache keys from hashable values, "
                        f"got non-hashable value {val!r} at context key {key!r} "
                        f"(dependency of field {field})"
                    ) from None  # we don't need to chain the exception created 2 lines above
                else:
                    return val