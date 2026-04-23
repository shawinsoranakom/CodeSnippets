def _instanciate_attrs(self, field_data):
        """ Return the parameters for a field instance for ``field_data``. """
        attrs = {
            'manual': True,
            'string': field_data['field_description'],
            'help': field_data['help'],
            'index': bool(field_data['index']),
            'copy': bool(field_data['copied']),
            'related': field_data['related'],
            'required': bool(field_data['required']),
            'readonly': bool(field_data['readonly']),
            'store': bool(field_data['store']),
            'company_dependent': bool(field_data['company_dependent']),
        }
        if field_data['ttype'] in ('char', 'text', 'html'):
            attrs['translate'] = FIELD_TRANSLATE.get(
                field_data['translate'],
                True
            )
            if field_data['ttype'] == 'char':
                attrs['size'] = field_data['size'] or None
            elif field_data['ttype'] == 'html':
                attrs['sanitize'] = field_data['sanitize']
                attrs['sanitize_overridable'] = field_data['sanitize_overridable']
                attrs['sanitize_tags'] = field_data['sanitize_tags']
                attrs['sanitize_attributes'] = field_data['sanitize_attributes']
                attrs['sanitize_style'] = field_data['sanitize_style']
                attrs['sanitize_form'] = field_data['sanitize_form']
                attrs['strip_style'] = field_data['strip_style']
                attrs['strip_classes'] = field_data['strip_classes']
        elif field_data['ttype'] in ('selection', 'reference'):
            attrs['selection'] = self.env['ir.model.fields.selection']._get_selection_data(field_data['id'])
            if field_data['ttype'] == 'selection':
                attrs['group_expand'] = field_data['group_expand']
        elif field_data['ttype'] == 'many2one':
            if not self.pool.loaded and field_data['relation'] not in self.env:
                return
            attrs['comodel_name'] = field_data['relation']
            attrs['ondelete'] = field_data['on_delete']
            attrs['domain'] = safe_eval(field_data['domain'] or '[]')
            attrs['group_expand'] = '_read_group_expand_full' if field_data['group_expand'] else None
        elif field_data['ttype'] == 'one2many':
            if not self.pool.loaded and not (
                field_data['relation'] in self.env and (
                    field_data['relation_field'] in self.env[field_data['relation']]._fields or
                    field_data['relation_field'] in self._get_manual_field_data(field_data['relation'])
            )):
                return
            attrs['comodel_name'] = field_data['relation']
            attrs['inverse_name'] = field_data['relation_field']
            attrs['domain'] = safe_eval(field_data['domain'] or '[]')
        elif field_data['ttype'] == 'many2many':
            if not self.pool.loaded and field_data['relation'] not in self.env:
                return
            attrs['comodel_name'] = field_data['relation']
            rel, col1, col2 = self._custom_many2many_names(field_data['model'], field_data['relation'])
            attrs['relation'] = field_data['relation_table'] or rel
            attrs['column1'] = field_data['column1'] or col1
            attrs['column2'] = field_data['column2'] or col2
            attrs['domain'] = safe_eval(field_data['domain'] or '[]')
        elif field_data['ttype'] == 'monetary':
            # be sure that custom monetary field are always instanciated
            if not self.pool.loaded and \
                field_data['currency_field'] and not self._is_manual_name(field_data['currency_field']):
                return
            attrs['currency_field'] = field_data['currency_field']
        # add compute function if given
        if field_data['compute']:
            attrs['compute'] = make_compute(field_data['compute'], field_data['depends'])
        return attrs