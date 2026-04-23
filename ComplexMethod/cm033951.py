def _add_host_to_keyed_groups(self, keys, variables, host, strict=False, fetch_hostvars=True):
        """ helper to create groups for plugins based on variable values and add the corresponding hosts to it"""
        should_default_value = (None, '')

        if keys and isinstance(keys, list):
            for keyed in keys:
                if keyed and isinstance(keyed, dict):

                    if fetch_hostvars:
                        variables = combine_vars(variables, self.inventory.get_host(host).get_vars())
                    try:
                        key = self._compose(keyed.get('key'), variables)
                    except Exception as e:
                        if strict:
                            raise AnsibleParserError("Could not generate group for host %s from %s entry: %s" % (host, keyed.get('key'), to_native(e)))
                        continue
                    default_value_name = keyed.get('default_value', None)
                    trailing_separator = keyed.get('trailing_separator')
                    if trailing_separator is not None and default_value_name is not None:
                        raise AnsibleParserError("parameters are mutually exclusive for keyed groups: default_value|trailing_separator")

                    use_default = key in should_default_value and default_value_name is not None
                    if key or use_default:
                        prefix = keyed.get('prefix', '')
                        sep = keyed.get('separator', '_')
                        raw_parent_name = keyed.get('parent_group', None)

                        try:
                            raw_parent_name = self.templar.template(raw_parent_name)
                        except AnsibleValueOmittedError:
                            raw_parent_name = None
                        except Exception as ex:
                            if strict:
                                raise AnsibleParserError(f'Could not generate parent group {raw_parent_name!r} for group {key!r}: {ex}') from ex

                            continue

                        new_raw_group_names = []
                        if use_default:
                            new_raw_group_names.append(default_value_name)
                        elif isinstance(key, str):
                            new_raw_group_names.append(key)
                        elif isinstance(key, list):
                            for name in key:
                                # if list item is empty, 'default_value' will be used as group name
                                if name in should_default_value and default_value_name is not None:
                                    new_raw_group_names.append(default_value_name)
                                else:
                                    new_raw_group_names.append(name)
                        elif isinstance(key, Mapping):
                            for (gname, gval) in key.items():
                                bare_name = '%s%s%s' % (gname, sep, gval)
                                if gval in should_default_value:
                                    # key's value is empty
                                    if default_value_name is not None:
                                        bare_name = '%s%s%s' % (gname, sep, default_value_name)
                                    elif trailing_separator is False:
                                        bare_name = gname
                                new_raw_group_names.append(bare_name)
                        else:
                            raise AnsibleParserError("Invalid group name format, expected a string or a list of them or dictionary, got: %s" % type(key))

                        for bare_name in new_raw_group_names:
                            if prefix == '' and self.get_option('leading_separator') is False:
                                sep = ''
                            gname = self._sanitize_group_name('%s%s%s' % (prefix, sep, bare_name))
                            result_gname = self.inventory.add_group(gname)
                            self.inventory.add_host(host, result_gname)

                            if raw_parent_name:
                                parent_name = self._sanitize_group_name(raw_parent_name)
                                self.inventory.add_group(parent_name)
                                self.inventory.add_child(parent_name, result_gname)

                    else:
                        # exclude case of empty list and dictionary, because these are valid constructions
                        # simply no groups need to be constructed, but are still falsy
                        if strict and key not in ([], {}):
                            raise AnsibleParserError("No key or key resulted empty for %s in host %s, invalid entry" % (keyed.get('key'), host))
                else:
                    raise AnsibleParserError("Invalid keyed group entry, it must be a dictionary: %s " % keyed)