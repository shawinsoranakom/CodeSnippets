def create(self, vals_list: list[ValuesType]) -> Self:
        """Create new records for the model.

        The new records are initialized using the values from the list of dicts
        ``vals_list``, and if necessary those from :meth:`~.default_get`.

        :param vals_list:
            values for the model's fields, as a list of dictionaries::

                [{'field_name': field_value, ...}, ...]

            For backward compatibility, ``vals_list`` may be a dictionary.
            It is treated as a singleton list ``[vals]``, and a single record
            is returned.

            see :meth:`~.write` for details

        :return: the created records
        :raise AccessError: if the current user is not allowed to create records of the specified model
        :raise ValidationError: if user tries to enter invalid value for a selection field
        :raise ValueError: if a field name specified in the create values does not exist.
        :raise UserError: if a loop would be created in a hierarchy of objects a result of the operation
          (such as setting an object as its own parent)
        """
        assert isinstance(vals_list, (list, tuple))
        if not vals_list:
            return self.browse()

        self = self.browse()
        self.check_access('create')

        # check access to all user-provided fields
        field_names = OrderedSet(fname for vals in vals_list for fname in vals)
        field_names.update(
            field_name
            for context_key in self.env.context
            if context_key.startswith('default_')
            and (field_name := context_key[8:])
            and field_name in self._fields
        )
        for field_name in field_names:
            field = self._fields.get(field_name)
            if field is None:
                raise ValueError(f"Invalid field {field_name!r} in {self._name!r}")
            self._check_field_access(field, 'write')

        new_vals_list = self._prepare_create_values(vals_list)

        # classify fields for each record
        data_list = []
        determine_inverses = defaultdict(OrderedSet)       # {inverse: fields}

        for vals in new_vals_list:
            precomputed = vals.pop('__precomputed__', ())

            # distribute fields into sets for various purposes
            data = {}
            data['stored'] = stored = {}
            data['inversed'] = inversed = {}
            data['inherited'] = inherited = defaultdict(dict)
            data['protected'] = protected = set()
            for key, val in vals.items():
                field = self._fields.get(key)
                if not field:
                    raise ValueError("Invalid field %r on model %r" % (key, self._name))
                if field.store:
                    stored[key] = val
                if field.inherited:
                    inherited[field.related_field.model_name][key] = val
                elif field.inverse and field not in precomputed:
                    inversed[key] = val
                    determine_inverses[field.inverse].add(field)
                # protect editable computed fields and precomputed fields
                # against (re)computation
                if field.compute and (not field.readonly or field.precompute):
                    protected.update(self.pool.field_computed.get(field, [field]))

            data_list.append(data)

        # create or update parent records
        for model_name, parent_name in self._inherits.items():
            parent_data_list = []
            for data in data_list:
                if not data['stored'].get(parent_name):
                    parent_data_list.append(data)
                elif data['inherited'][model_name]:
                    parent = self.env[model_name].browse(data['stored'][parent_name])
                    parent.write(data['inherited'][model_name])

            if parent_data_list:
                parents = self.env[model_name].create([
                    data['inherited'][model_name]
                    for data in parent_data_list
                ])
                for parent, data in zip(parents, parent_data_list):
                    data['stored'][parent_name] = parent.id

        # create records with stored fields
        records = self._create(data_list)

        # protect fields being written against recomputation
        protected_fields = [(data['protected'], data['record']) for data in data_list]
        with self.env.protecting(protected_fields):
            # call inverse method for each group of fields
            for fields in determine_inverses.values():
                # determine which records to inverse for those fields
                inv_names = {field.name for field in fields}
                inv_rec_ids = []
                for data in data_list:
                    if inv_names.isdisjoint(data['inversed']):
                        continue
                    record = data['record']
                    record._update_cache({
                        fname: value
                        for fname, value in data['inversed'].items()
                        if fname in inv_names and fname not in data['stored']
                    })
                    inv_rec_ids.append(record.id)

                inv_records = self.browse(inv_rec_ids)
                next(iter(fields)).determine_inverse(inv_records)
                # Values of non-stored fields were cached before running inverse methods. In case of x2many create
                # commands, the cache may therefore hold NewId records. We must now invalidate those values.
                inv_relational_fnames = [field.name for field in fields if field.type in ('one2many', 'many2many') and not field.store]
                inv_records.invalidate_recordset(fnames=inv_relational_fnames)

        # check Python constraints for non-stored inversed fields
        for data in data_list:
            data['record']._validate_fields(data['inversed'], data['stored'])

        if self._check_company_auto:
            records._check_company()

        import_module = self.env.context.get('_import_current_module')
        if not import_module: # not an import -> bail
            return records

        # It is to support setting xids directly in create by
        # providing an "id" key (otherwise stripped by create) during an import
        # (which should strip 'id' from the input data anyway)
        noupdate = self.env.context.get('noupdate', False)

        xids = (v.get('id') for v in vals_list)
        self.env['ir.model.data']._update_xmlids([
            {
                'xml_id': xid if '.' in xid else ('%s.%s' % (import_module, xid)),
                'record': rec,
                # note: this is not used when updating o2ms above...
                'noupdate': noupdate,
            }
            for rec, xid in zip(records, xids)
            if xid and isinstance(xid, str)
        ])

        return records