def _process_ondelete(self):
        """ Process the 'ondelete' of the given selection values. """
        def safe_write(records, fname, value):
            if not records:
                return
            try:
                with self.env.cr.savepoint():
                    records.write({fname: value})
            except Exception:
                # going through the ORM failed, probably because of an exception
                # in an override or possibly a constraint.
                _logger.runbot(
                    "Could not fulfill ondelete action for field %s.%s, "
                    "attempting ORM bypass...", records._name, fname,
                )
                # if this fails then we're shit out of luck and there's nothing
                # we can do except fix on a case-by-case basis
                self.env.execute_query(SQL(
                    "UPDATE %s SET %s=%s WHERE id IN %s",
                    SQL.identifier(records._table),
                    SQL.identifier(fname),
                    field.convert_to_column_insert(value, records),
                    records._ids,
                ))
                records.invalidate_recordset([fname])

        for selection in self:
            # The field may exist in database but not in registry. In this case
            # we allow the field to be skipped, but for production this should
            # be handled through a migration script. The ORM will take care of
            # the orphaned 'ir.model.fields' down the stack, and will log a
            # warning prompting the developer to write a migration script.
            Model = self.env.get(selection.field_id.model)
            if Model is None:
                continue
            field = Model._fields.get(selection.field_id.name)
            if not field or not field.store or not Model._auto:
                continue

            # Field changed its type, skip it.
            if field.type not in ('selection', 'reference'):
                continue

            ondelete = (field.ondelete or {}).get(selection.value)
            # special case for custom fields
            if ondelete is None and field.manual and not field.required:
                ondelete = 'set null'

            if ondelete is None:
                # nothing to do, the selection does not come from a field extension
                continue

            companies = self.env.companies if self.field_id.company_dependent else [self.env.company]
            for company in companies:
                # make a company-specific env for the Model and selection
                Model = Model.with_company(company.id)
                selection = selection.with_company(company.id)
                if callable(ondelete):
                    ondelete(selection._get_records())
                elif ondelete == 'set null':
                    safe_write(selection._get_records(), field.name, False)
                elif ondelete == 'set default':
                    value = field.convert_to_write(field.default(Model), Model)
                    safe_write(selection._get_records(), field.name, value)
                elif ondelete.startswith('set '):
                    safe_write(selection._get_records(), field.name, ondelete[4:])
                elif ondelete == 'cascade':
                    selection._get_records().unlink()
                else:
                    # this shouldn't happen... simply a sanity check
                    raise ValueError(_(
                        'The ondelete policy "%(policy)s" is not valid for field "%(field)s"',
                        policy=ondelete, field=selection,
                    ))