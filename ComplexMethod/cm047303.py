def _prepare_update(self):
        """ Check whether the fields in ``self`` may be modified or removed.
            This method prevents the modification/deletion of many2one fields
            that have an inverse one2many, for instance.
        """
        from odoo.orm.model_classes import pop_field

        uninstalling = self.env.context.get(MODULE_UNINSTALL_FLAG)
        if not uninstalling and any(record.state != 'manual' for record in self):
            raise UserError(_("This column contains module data and cannot be removed!"))

        records = self              # all the records to delete
        fields_ = OrderedSet()      # all the fields corresponding to 'records'
        failed_dependencies = []    # list of broken (field, dependent_field)

        for record in self:
            model = self.env.get(record.model)
            if model is None:
                continue
            field = model._fields.get(record.name)
            if field is None:
                continue
            fields_.add(field)
            for dep in self.pool.get_dependent_fields(field):
                if dep.manual:
                    failed_dependencies.append((field, dep))
                elif dep.inherited:
                    fields_.add(dep)
                    records |= self._get(dep.model_name, dep.name)

        for field in fields_:
            for inverse in model.pool.field_inverses[field]:
                if inverse.manual and inverse.type == 'one2many':
                    failed_dependencies.append((field, inverse))

        self = records

        if failed_dependencies:
            if not uninstalling:
                field, dep = failed_dependencies[0]
                raise UserError(_(
                    "The field '%(field)s' cannot be removed because the field '%(other_field)s' depends on it.",
                    field=field, other_field=dep,
                ))
            else:
                self = self.union(*[
                    self._get(dep.model_name, dep.name)
                    for field, dep in failed_dependencies
                ])

        records = self.filtered(lambda record: record.state == 'manual')
        if not records:
            return self

        # remove pending write of this field
        # DLE P16: if there are pending updates of the field we currently try to unlink, pop them out from the cache
        # test `test_unlink_with_dependant`
        for record in records:
            model = self.env.get(record.model)
            field = model and model._fields.get(record.name)
            if field:
                self.env._field_dirty.pop(field)
        # remove fields from registry, and check that views are not broken
        fields = [pop_field(self.env.registry[record.model], record.name) for record in records]
        domain = Domain.OR([('arch_db', 'like', record.name)] for record in records)
        views = self.env['ir.ui.view'].search(domain)
        try:
            for view in views:
                view._check_xml()
        except Exception:
            if not uninstalling:
                raise UserError(_(
                    "Cannot rename/delete fields that are still present in views:\nFields: %(fields)s\nView: %(view)s",
                    fields=fields,
                    view=view.name,
                ))
            else:
                # uninstall mode
                _logger.warning(
                    "The following fields were force-deleted to prevent a registry crash %s the following view might be broken %s",
                    ", ".join(str(f) for f in fields),
                    view.name)
        finally:
            if not uninstalling:
                # the registry has been modified, restore it
                self.pool._setup_models__(self.env.cr)

        return self