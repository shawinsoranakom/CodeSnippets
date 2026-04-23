def __get__(self, obj, obj_type=None):
        if getattr(obj, '_squashed', False) or getattr(obj, '_finalized', False):
            value = getattr(obj, f'_{self.name}', Sentinel)
        else:
            try:
                value = obj._get_parent_attribute(self.name)
            except AttributeError:
                method = f'_get_attr_{self.name}'
                if hasattr(obj, method):
                    # NOTE this appears to be not needed in the codebase,
                    # _get_attr_connection has been replaced by ConnectionFieldAttribute.
                    # Leaving it here for test_attr_method from
                    # test/units/playbook/test_base.py to pass and for backwards compat.
                    if getattr(obj, '_squashed', False):
                        value = getattr(obj, f'_{self.name}', Sentinel)
                    else:
                        value = getattr(obj, method)()
                else:
                    value = getattr(obj, f'_{self.name}', Sentinel)

        if value is Sentinel:
            value = self.default
            if callable(value):
                value = value()

        return value