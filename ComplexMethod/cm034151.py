def _get_parent_attribute(self, attr, omit=False):
        """
        Generic logic to get the attribute or parent attribute for a block value.
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
                try:
                    if getattr(_parent, 'statically_loaded', True):
                        if hasattr(_parent, '_get_parent_attribute'):
                            parent_value = _parent._get_parent_attribute(attr)
                        else:
                            parent_value = getattr(_parent, f'_{attr}', Sentinel)
                        if extend:
                            value = self._extend_value(value, parent_value, prepend)
                        else:
                            value = parent_value
                except AttributeError:
                    pass
            if self._role and (value is Sentinel or extend):
                try:
                    parent_value = getattr(self._role, f'_{attr}', Sentinel)
                    if extend:
                        value = self._extend_value(value, parent_value, prepend)
                    else:
                        value = parent_value

                    dep_chain = self.get_dep_chain()
                    if dep_chain and (value is Sentinel or extend):
                        dep_chain.reverse()
                        for dep in dep_chain:
                            dep_value = getattr(dep, f'_{attr}', Sentinel)
                            if extend:
                                value = self._extend_value(value, dep_value, prepend)
                            else:
                                value = dep_value

                            if value is not Sentinel and not extend:
                                break
                except AttributeError:
                    pass
            if self._play and (value is Sentinel or extend):
                try:
                    play_value = getattr(self._play, f'_{attr}', Sentinel)
                    if play_value is not Sentinel:
                        if extend:
                            value = self._extend_value(value, play_value, prepend)
                        else:
                            value = play_value
                except AttributeError:
                    pass
        except KeyError:
            pass

        return value