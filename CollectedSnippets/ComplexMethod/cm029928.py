def __setitem__(self, key, value):
        """
        Changes anything not dundered or not a descriptor.

        If an enum member name is used twice, an error is raised; duplicate
        values are not checked for.

        Single underscore (sunder) names are reserved.
        """
        if self._cls_name is not None and _is_private(self._cls_name, key):
            # do nothing, name will be a normal attribute
            pass
        elif _is_sunder(key):
            if key not in (
                    '_order_',
                    '_generate_next_value_', '_numeric_repr_', '_missing_', '_ignore_',
                    '_iter_member_', '_iter_member_by_value_', '_iter_member_by_def_',
                    '_add_alias_', '_add_value_alias_',
                    # While not in use internally, those are common for pretty
                    # printing and thus excluded from Enum's reservation of
                    # _sunder_ names
                    ) and not key.startswith('_repr_'):
                raise ValueError(
                        '_sunder_ names, such as %r, are reserved for future Enum use'
                        % (key, )
                        )
            if key == '_generate_next_value_':
                # check if members already defined as auto()
                if self._auto_called:
                    raise TypeError("_generate_next_value_ must be defined before members")
                _gnv = value.__func__ if isinstance(value, staticmethod) else value
                setattr(self, '_generate_next_value', _gnv)
            elif key == '_ignore_':
                if isinstance(value, str):
                    value = value.replace(',',' ').split()
                else:
                    value = list(value)
                self._ignore = value
                already = set(value) & set(self._member_names)
                if already:
                    raise ValueError(
                            '_ignore_ cannot specify already set names: %r'
                            % (already, )
                            )
        elif _is_dunder(key):
            if key == '__order__':
                key = '_order_'
        elif key in self._member_names:
            # descriptor overwriting an enum?
            raise TypeError('%r already defined as %r' % (key, self[key]))
        elif key in self._ignore:
            pass
        elif isinstance(value, nonmember):
            # unwrap value here; it won't be processed by the below `else`
            value = value.value
        elif _is_descriptor(value):
            pass
        elif self._cls_name is not None and _is_internal_class(self._cls_name, value):
            # do nothing, name will be a normal attribute
            pass
        else:
            if key in self:
                # enum overwriting a descriptor?
                raise TypeError('%r already defined as %r' % (key, self[key]))
            elif isinstance(value, member):
                # unwrap value here -- it will become a member
                value = value.value
            non_auto_store = True
            single = False
            if isinstance(value, auto):
                single = True
                value = (value, )
            if isinstance(value, tuple) and any(isinstance(v, auto) for v in value):
                # insist on an actual tuple, no subclasses, in keeping with only supporting
                # top-level auto() usage (not contained in any other data structure)
                auto_valued = []
                t = type(value)
                for v in value:
                    if isinstance(v, auto):
                        non_auto_store = False
                        if v.value == _auto_null:
                            v.value = self._generate_next_value(
                                    key, 1, len(self._member_names), self._last_values[:],
                                    )
                            self._auto_called = True
                        v = v.value
                        self._last_values.append(v)
                    auto_valued.append(v)
                if single:
                    value = auto_valued[0]
                else:
                    try:
                        # accepts iterable as multiple arguments?
                        value = t(auto_valued)
                    except TypeError:
                        # then pass them in singly
                        value = t(*auto_valued)
            self._member_names[key] = None
            if non_auto_store:
                self._last_values.append(value)
        super().__setitem__(key, value)