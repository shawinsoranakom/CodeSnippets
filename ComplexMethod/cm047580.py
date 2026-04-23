def write(self, vals: ValuesType) -> typing.Literal[True]:
        """ Update all records in ``self`` with the provided values.

        :param vals: fields to update and the value to set on them
        :raise AccessError: if user is not allowed to modify the specified records/fields
        :raise ValidationError: if invalid values are specified for selection fields
        :raise UserError: if a loop would be created in a hierarchy of objects a result of the operation (such as setting an object as its own parent)

        * For numeric fields (:class:`~odoo.fields.Integer`,
          :class:`~odoo.fields.Float`) the value should be of the
          corresponding type
        * For :class:`~odoo.fields.Boolean`, the value should be a
          :class:`python:bool`
        * For :class:`~odoo.fields.Selection`, the value should match the
          selection values (generally :class:`python:str`, sometimes
          :class:`python:int`)
        * For :class:`~odoo.fields.Many2one`, the value should be the
          database identifier of the record to set
        * The expected value of a :class:`~odoo.fields.One2many` or
          :class:`~odoo.fields.Many2many` relational field is a list of
          :class:`~odoo.fields.Command` that manipulate the relation the
          implement. There are a total of 7 commands:
          :meth:`~odoo.fields.Command.create`,
          :meth:`~odoo.fields.Command.update`,
          :meth:`~odoo.fields.Command.delete`,
          :meth:`~odoo.fields.Command.unlink`,
          :meth:`~odoo.fields.Command.link`,
          :meth:`~odoo.fields.Command.clear`, and
          :meth:`~odoo.fields.Command.set`.
        * For :class:`~odoo.fields.Date` and `~odoo.fields.Datetime`,
          the value should be either a date(time), or a string.

          .. warning::

            If a string is provided for Date(time) fields,
            it must be UTC-only and formatted according to
            :const:`odoo.tools.misc.DEFAULT_SERVER_DATE_FORMAT` and
            :const:`odoo.tools.misc.DEFAULT_SERVER_DATETIME_FORMAT`

        * Other non-relational fields use a string for value
        """
        if not self:
            return True

        self.check_access('write')
        for field_name in vals:
            try:
                self._check_field_access(self._fields[field_name], 'write')
            except KeyError as e:
                raise ValueError(f"Invalid field {field_name!r} in {self._name!r}") from e
        env = self.env

        bad_names = {'id', 'parent_path'}
        if self._log_access:
            # the superuser can set log_access fields while loading registry
            if not (self.env.uid == SUPERUSER_ID and not self.pool.ready):
                bad_names.update(LOG_ACCESS_COLUMNS)

        # set magic fields
        vals = {key: val for key, val in vals.items() if key not in bad_names}
        if self._log_access:
            vals.setdefault('write_uid', self.env.uid)
            vals.setdefault('write_date', self.env.cr.now())

        field_values = []                           # [(field, value)]
        determine_inverses = defaultdict(list)      # {inverse: fields}
        fnames_modifying_relations = []
        protected = set()
        for fname, value in vals.items():
            field = self._fields.get(fname)
            if not field:
                raise ValueError("Invalid field %r on model %r" % (fname, self._name))
            field_values.append((field, value))
            if field.inverse:
                if field.type in ('one2many', 'many2many'):
                    # The written value is a list of commands that must applied
                    # on the field's current value. Because the field is
                    # protected while being written, the field's current value
                    # will not be computed and default to an empty recordset. So
                    # make sure the field's value is in cache before writing, in
                    # order to avoid an inconsistent update.
                    self[fname]
                determine_inverses[field.inverse].append(field)
            if self.pool.is_modifying_relations(field):
                fnames_modifying_relations.append(fname)
            if field.inverse or (field.compute and not field.readonly):
                if field.store or field.type not in ('one2many', 'many2many'):
                    # Protect the field from being recomputed while being
                    # inversed. In the case of non-stored x2many fields, the
                    # field's value may contain unexpeced new records (created
                    # by command 0). Those new records are necessary for
                    # inversing the field, but should no longer appear if the
                    # field is recomputed afterwards. Not protecting the field
                    # will automatically invalidate the field from the cache,
                    # forcing its value to be recomputed once dependencies are
                    # up-to-date.
                    protected.update(self.pool.field_computed.get(field, [field]))

        # force the computation of fields that are computed with some assigned
        # fields, but are not assigned themselves
        to_compute = [field.name
                      for field in protected
                      if field.compute and field.name not in vals]
        if to_compute:
            self._recompute_recordset(to_compute)

        # protect fields being written against recomputation
        with env.protecting(protected, self):
            # Determine records depending on values. When modifying a relational
            # field, you have to recompute what depends on the field's values
            # before and after modification.  This is because the modification
            # has an impact on the "data path" between a computed field and its
            # dependency.  Note that this double call to modified() is only
            # necessary for relational fields.
            #
            # It is best explained with a simple example: consider two sales
            # orders SO1 and SO2.  The computed total amount on sales orders
            # indirectly depends on the many2one field 'order_id' linking lines
            # to their sales order.  Now consider the following code:
            #
            #   line = so1.line_ids[0]      # pick a line from SO1
            #   line.order_id = so2         # move the line to SO2
            #
            # In this situation, the total amount must be recomputed on *both*
            # sales order: the line's order before the modification, and the
            # line's order after the modification.
            self.modified(fnames_modifying_relations, before=True)

            real_recs = self.filtered('id')

            # field.write_sequence determines a priority for writing on fields.
            # Monetary fields need their corresponding currency field in cache
            # for rounding values. X2many fields must be written last, because
            # they flush other fields when deleting lines.
            for field, value in sorted(field_values, key=lambda item: item[0].write_sequence):
                field.write(self, value)

            # determine records depending on new values
            #
            # Call modified after write, because the modified can trigger a
            # search which can trigger a flush which can trigger a recompute
            # which remove the field from the recompute list while all the
            # values required for the computation could not be yet in cache.
            # e.g. Write on `name` of `res.partner` trigger the recompute of
            # `display_name`, which triggers a search on child_ids to find the
            # childs to which the display_name must be recomputed, which
            # triggers the flush of `display_name` because the _order of
            # res.partner includes display_name. The computation of display_name
            # is then done too soon because the parent_id was not yet written.
            # (`test_01_website_reset_password_tour`)
            self.modified(vals)

            if self._parent_store and self._parent_name in vals:
                self.flush_model([self._parent_name])

            # validate non-inversed fields first
            inverse_fields = [f.name for fs in determine_inverses.values() for f in fs]
            real_recs._validate_fields(vals, inverse_fields)

            for fields in determine_inverses.values():
                # write again on non-stored fields that have been invalidated from cache
                for field in fields:
                    if not field.store and (not field.inherited or field.type not in ('one2many', 'many2many')) and any(field._cache_missing_ids(real_recs)):
                        field.write(real_recs, vals[field.name])

                # inverse records that are not being computed
                try:
                    fields[0].determine_inverse(real_recs)
                except AccessError as e:
                    if fields[0].inherited:
                        description = self.env['ir.model']._get(self._name).name
                        raise AccessError(_(
                            "%(previous_message)s\n\nImplicitly accessed through '%(document_kind)s' (%(document_model)s).",
                            previous_message=e.args[0],
                            document_kind=description,
                            document_model=self._name,
                        ))
                    raise

            # validate inversed fields
            real_recs._validate_fields(inverse_fields)

        if self._check_company_auto:
            self._check_company(list(vals))
        return True