def _get_parent_attribute(self, attr, omit=False):
        """
        Generic logic to get the attribute or parent attribute for a task value.
        """
        fattr = self.fattributes[attr]

        extend = fattr.extend
        prepend = fattr.prepend

        try:
            # omit self, and only get parent values
            if omit:
                value = Sentinel
            else:
                value = getattr(self, f'_{attr}', Sentinel)

            # If parent is static, we can grab attrs from the parent
            # otherwise, defer to the grandparent
            if getattr(self._parent, 'statically_loaded', True):
                _parent = self._parent
            else:
                _parent = self._parent._parent

            if _parent and (value is Sentinel or extend):
                if getattr(_parent, 'statically_loaded', True):
                    # vars are always inheritable, other attributes might not be for the parent but still should be for other ancestors
                    if attr != 'vars' and hasattr(_parent, '_get_parent_attribute'):
                        parent_value = _parent._get_parent_attribute(attr)
                    else:
                        parent_value = getattr(_parent, f'_{attr}', Sentinel)

                    if extend:
                        value = self._extend_value(value, parent_value, prepend)
                    else:
                        value = parent_value
        except KeyError:
            pass

        return value