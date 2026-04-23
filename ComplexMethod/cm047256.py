def db_id_for(self, model, field, subfield, value, savepoint):
        """ Finds a database id for the reference ``value`` in the referencing
        subfield ``subfield`` of the provided field of the provided model.

        :param model: model to which the field belongs
        :param field: relational field for which references are provided
        :param subfield: a relational subfield allowing building of refs to
                         existing records: ``None`` for a name_search,
                         ``id`` for an external id and ``.id`` for a database
                         id
        :param value: value of the reference to match to an actual record
        :param savepoint: savepoint for rollback on errors
        :return: a pair of the matched database identifier (if any), the
                 translated user-readable name for the field and the list of
                 warnings
        :rtype: (ID|None, unicode, list)
        """
        # the function 'flush' comes from BaseModel.load(), and forces the
        # creation/update of former records (batch creation)
        flush = self.env.context.get('import_flush', lambda **kw: None)

        id = None
        warnings = []
        error_msg = ''
        action = {
            'name': 'Possible Values',
            'type': 'ir.actions.act_window', 'target': 'new',
            'view_mode': 'list,form',
            'views': [(False, 'list'), (False, 'form')],
            'context': {'create': False},
            'help': self.env._("See all possible values")}
        if subfield is None:
            action['res_model'] = field.comodel_name
        elif subfield in ('id', '.id'):
            action['res_model'] = 'ir.model.data'
            action['domain'] = [('model', '=', field.comodel_name)]

        RelatedModel = self.env[field.comodel_name]
        if subfield == '.id':
            field_type = self.env._("database id")
            if isinstance(value, str) and not self._str_to_boolean(model, field, value, savepoint=savepoint)[0]:
                return False, warnings
            try:
                tentative_id = int(value)
            except ValueError:
                raise self._format_import_error(
                    ValueError,
                    self.env._("Invalid database id '%s' for the field '%%(field)s'"),
                    value,
                    {'moreinfo': action})
            if RelatedModel.browse(tentative_id).exists():
                id = tentative_id
        elif subfield == 'id':
            field_type = self.env._("external id")
            if not self._str_to_boolean(model, field, value, savepoint=savepoint)[0]:
                return False, warnings
            if '.' in value:
                xmlid = value
            else:
                xmlid = "%s.%s" % (self.env.context.get('_import_current_module', ''), value)
            flush(xml_id=xmlid)
            id = self._xmlid_to_record_id(xmlid, RelatedModel)
        elif subfield is None:
            field_type = self.env._("name")
            if value == '':
                return False, warnings
            flush(model=field.comodel_name)
            ids = RelatedModel.name_search(name=value, operator='=')
            if ids:
                if len(ids) > 1:
                    warnings.append(ImportWarning(_(
                        'Found multiple matches for value "%(value)s" in field "%%(field)s" (%(match_count)s matches)',
                        value=str(value).replace('%', '%%'),
                        match_count=len(ids),
                    )))
                id, _name = ids[0]
            else:
                name_create_enabled_fields = self.env.context.get('name_create_enabled_fields') or {}
                if name_create_enabled_fields.get(field.name):
                    try:
                        id, _name = RelatedModel.name_create(name=value)
                        RelatedModel.env.flush_all()
                    except Exception:  # noqa: BLE001
                        savepoint.rollback()
                        error_msg = self.env._("Cannot create new '%s' records from their name alone. Please create those records manually and try importing again.", RelatedModel._description)
        else:
            raise self._format_import_error(
                Exception,
                self.env._("Unknown sub-field “%s”", subfield),
            )

        set_empty = False
        skip_record = False
        if self.env.context.get('import_file'):
            import_set_empty_fields = self.env.context.get('import_set_empty_fields') or []
            field_path = "/".join((self.env.context.get('parent_fields_hierarchy', []) + [field.name]))
            set_empty = field_path in import_set_empty_fields
            skip_record = field_path in self.env.context.get('import_skip_records', [])
        if id is None and not set_empty and not skip_record:
            if error_msg:
                message = self.env._("No matching record found for %(field_type)s '%(value)s' in field '%%(field)s' and the following error was encountered when we attempted to create one: %(error_message)s")
            else:
                message = self.env._("No matching record found for %(field_type)s '%(value)s' in field '%%(field)s'")

            error_info_dict = {'moreinfo': action}
            if self.env.context.get('import_file'):
                # limit to 50 char to avoid too long error messages.
                value = value[:50] if isinstance(value, str) else value
                error_info_dict.update({'value': value, 'field_type': field_type})
                if error_msg:
                    error_info_dict['error_message'] = error_msg
            raise self._format_import_error(
                ValueError,
                message,
                {'field_type': field_type, 'value': value, 'error_message': error_msg},
                error_info_dict)
        return id, warnings