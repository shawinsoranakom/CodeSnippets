def _setup_attrs__(self, model_class, name):
        super()._setup_attrs__(model_class, name)
        if not self._base_fields__:
            return

        # determine selection (applying 'selection_add' extensions) as a dict
        values = None

        for field in self._base_fields__:
            # We cannot use field.selection or field.selection_add here
            # because those attributes are overridden by ``_setup_attrs__``.
            if 'selection' in field._args__:
                if self.related:
                    _logger.warning("%s: selection attribute will be ignored as the field is related", self)
                selection = field._args__['selection']
                if isinstance(selection, (list, tuple)):
                    if values is not None and list(values) != [kv[0] for kv in selection]:
                        _logger.warning("%s: selection=%r overrides existing selection; use selection_add instead", self, selection)
                    values = dict(selection)
                    self.ondelete = {}
                elif callable(selection) or isinstance(selection, str):
                    self.ondelete = None
                    self.selection = selection
                    values = None
                else:
                    raise ValueError(f"{self!r}: selection={selection!r} should be a list, a callable or a method name")

            if 'selection_add' in field._args__:
                if self.related:
                    _logger.warning("%s: selection_add attribute will be ignored as the field is related", self)
                selection_add = field._args__['selection_add']
                assert isinstance(selection_add, list), \
                    "%s: selection_add=%r must be a list" % (self, selection_add)
                assert values is not None, \
                    "%s: selection_add=%r on non-list selection %r" % (self, selection_add, self.selection)

                values_add = {kv[0]: (kv[1] if len(kv) > 1 else None) for kv in selection_add}
                ondelete = field._args__.get('ondelete') or {}
                new_values = [key for key in values_add if key not in values]
                for key in new_values:
                    ondelete.setdefault(key, 'set null')
                if self.required and new_values and 'set null' in ondelete.values():
                    raise ValueError(
                        "%r: required selection fields must define an ondelete policy that "
                        "implements the proper cleanup of the corresponding records upon "
                        "module uninstallation. Please use one or more of the following "
                        "policies: 'set default' (if the field has a default defined), 'cascade', "
                        "or a single-argument callable where the argument is the recordset "
                        "containing the specified option." % self
                    )

                # check ondelete values
                for key, val in ondelete.items():
                    if callable(val) or val in ('set null', 'cascade'):
                        continue
                    if val == 'set default':
                        assert self.default is not None, (
                            "%r: ondelete policy of type 'set default' is invalid for this field "
                            "as it does not define a default! Either define one in the base "
                            "field, or change the chosen ondelete policy" % self
                        )
                    elif val.startswith('set '):
                        assert val[4:] in values, (
                            "%s: ondelete policy of type 'set %%' must be either 'set null', "
                            "'set default', or 'set value' where value is a valid selection value."
                        ) % self
                    else:
                        raise ValueError(
                            "%r: ondelete policy %r for selection value %r is not a valid ondelete"
                            " policy, please choose one of 'set null', 'set default', "
                            "'set [value]', 'cascade' or a callable" % (self, val, key)
                        )

                values = {
                    key: values_add.get(key) or values[key]
                    for key in merge_sequences(values, values_add)
                }
                self.ondelete.update(ondelete)

        if values is not None:
            self.selection = list(values.items())
            assert all(isinstance(key, str) for key in values), \
                "Field %s with non-str value in selection" % self

        self._selection = values