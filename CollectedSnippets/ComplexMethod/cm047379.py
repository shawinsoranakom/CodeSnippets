def create(self, vals_list):
        valid_types = self._fields['type']._selection
        for values in vals_list:
            if 'arch_db' in values and not values['arch_db']:
                # delete empty arch_db to avoid triggering _check_xml before _inverse_arch_base is called
                del values['arch_db']

            if not values.get('type'):
                if values.get('inherit_id'):
                    values['type'] = self.browse(values['inherit_id']).type
                else:

                    try:
                        if not values.get('arch') and not values.get('arch_base'):
                            raise ValidationError(_('Missing view architecture.'))
                        values['type'] = etree.fromstring(values.get('arch') or values.get('arch_base')).tag
                        if values['type'] not in valid_types:
                            raise ValidationError(_(
                                "Invalid view type: '%(view_type)s'.\n"
                                "You might have used an invalid starting tag in the architecture.\n"
                                "Allowed types are: %(valid_types)s",
                                view_type=values['type'], valid_types=', '.join(valid_types)
                            ))
                    except (etree.ParseError, ValueError):
                        # don't raise here, the constraint that runs `self._check_xml` will
                        # do the job properly.
                        pass
            if not values.get('key') and values.get('type') == 'qweb':
                values['key'] = "gen_key.%s" % str(uuid.uuid4())[:6]
            if not values.get('name'):
                values['name'] = "%s %s" % (values.get('model'), values['type'])
            # Create might be called with either `arch` (xml files), `arch_base` (form view) or `arch_db`.
            values['arch_prev'] = values.get('arch_base') or values.get('arch_db') or values.get('arch')
            # write on arch: bypass _inverse_arch()
            if 'arch' in values:
                values['arch_db'] = values.pop('arch')
                if 'install_filename' in self.env.context:
                    # we store the relative path to the resource instead of the absolute path, if found
                    # (it will be missing e.g. when importing data-only modules using base_import_module)
                    path_info = get_resource_from_path(self.env.context['install_filename'])
                    if path_info:
                        values['arch_fs'] = '/'.join(path_info[0:2])
                        values['arch_updated'] = False
            values.update(self._compute_defaults(values))

        self.env.registry.clear_cache('templates')
        result = super().create(vals_list)
        result.with_context(ir_ui_view_partial_validation=True)._check_xml()
        return result