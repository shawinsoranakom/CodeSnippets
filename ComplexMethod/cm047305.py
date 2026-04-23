def write(self, vals):
        if not self:
            return True

        # if set, *one* column can be renamed here
        column_rename = None

        # names of the models to patch
        patched_models = set()
        translate_only = all(self._fields[field_name].translate for field_name in vals)
        if vals and self and not translate_only:
            for item in self:
                if item.state != 'manual':
                    raise UserError(_('Properties of base fields cannot be altered in this manner! '
                                      'Please modify them through Python code, '
                                      'preferably through a custom addon!'))

                if vals.get('model_id', item.model_id.id) != item.model_id.id:
                    raise UserError(_("Changing the model of a field is forbidden!"))

                if vals.get('ttype', item.ttype) != item.ttype:
                    raise UserError(_("Changing the type of a field is not yet supported. "
                                      "Please drop it and create it again!"))

                obj = self.pool.get(item.model)
                field = getattr(obj, '_fields', {}).get(item.name)

                if vals.get('name', item.name) != item.name:
                    # We need to rename the field
                    item._prepare_update()
                    if item.ttype in ('one2many', 'many2many', 'binary'):
                        # those field names are not explicit in the database!
                        pass
                    else:
                        if column_rename:
                            raise UserError(_('Can only rename one field at a time!'))
                        column_rename = (obj._table, item.name, vals['name'], item.index, item.store)

                # We don't check the 'state', because it might come from the context
                # (thus be set for multiple fields) and will be ignored anyway.
                if obj is not None and field is not None:
                    patched_models.add(obj._name)

        # These shall never be written (modified)
        for column_name in ('model_id', 'model', 'state'):
            if column_name in vals:
                del vals[column_name]

        if vals.get('translate') and not isinstance(vals['translate'], str):
            _logger.warning("Deprecated since Odoo 19, ir.model.fields.translate becomes Selection, the value should be a string")
            vals['translate'] = 'html_translate' if vals.get('ttype') == 'html' else 'standard'

        if column_rename and self.state == 'manual':
            # renaming a studio field, remove inherits fields
            # we need to set the uninstall flag to allow removing them
            (self._prepare_update() - self).with_context(**{MODULE_UNINSTALL_FLAG: True}).unlink()

        res = super(IrModelFields, self).write(vals)

        self.env.flush_all()

        if column_rename:
            # rename column in database, and its corresponding index if present
            table, oldname, newname, index, stored = column_rename
            if stored:
                self.env.cr.execute(SQL(
                    'ALTER TABLE %s RENAME COLUMN %s TO %s',
                    SQL.identifier(table),
                    SQL.identifier(oldname),
                    SQL.identifier(newname)
                ))
                if index:
                    self.env.cr.execute(SQL(
                        'ALTER INDEX %s RENAME TO %s',
                        SQL.identifier(f'{table}_{oldname}_index'),
                        SQL.identifier(f'{table}_{newname}_index'),
                    ))

        if column_rename or patched_models or translate_only:
            # setup models, this will reload all manual fields in registry
            self.env.flush_all()
            model_names = OrderedSet(self.mapped('model'))
            self.pool._setup_models__(self.env.cr, model_names)

        if patched_models:
            # update the database schema of the models to patch
            models = self.pool.descendants(patched_models, '_inherits')
            self.pool.init_models(self.env.cr, models, dict(self.env.context, update_custom_fields=True))

        return res