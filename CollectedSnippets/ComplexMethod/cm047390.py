def _add_missing_fields(self, node, name_manager):
        """ Add the fields required for evaluating expressions in the view given by ``node``. """
        root = node
        missing_fields = name_manager.get_missing_fields()
        for name, (missing_groups, reasons) in missing_fields.items():
            if name not in name_manager.field_info:
                continue

            # If the available fields have different groups then to avoid it being missing for
            # certain users, we virtually add a field with common groups.
            name_manager.available_fields[name].setdefault('info', {})
            name_manager.available_fields[name].setdefault('groups', []).append(missing_groups)
            name_manager.available_names.add(name)

            readonly = True
            if filename_reasons := [r for r in reasons if r[1][0] == "filename"]:
                node = filename_reasons[-1][2]
                if node_readonly := node.get("readonly"):
                    readonly = node_readonly
                else:
                    field = name_manager.model._fields[node.get("name")]
                    if field.type == "binary":
                        readonly = field.readonly or False
            # If the field is not in the view without any group restriction,
            # add the field node with all mandatory groups (or without group if
            # the mandatory field does not have groups).
            attrs = {
                'name': name,
                'invisible' if root.tag != 'list' else 'column_invisible': 'True',
                'readonly': str(readonly),
                'data-used-by': '; '.join(
                    f"{attr}={expr!r} ({node.tag},{node.get('name')})"
                    for _groups, (attr, expr), node in reasons
                ),
            }

            if missing_groups is not False:
                subset_groups = missing_groups.invert_intersect(name_manager.model_groups)
                if subset_groups is None:
                    subset_groups = missing_groups
                if not subset_groups.is_universal():
                    attrs['__groups_key__'] = subset_groups.key

            item = etree.Element('field', attrs)
            item.tail = '\n'
            root.append(item)
        return missing_fields