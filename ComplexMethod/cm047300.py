def _check_depends(self):
        """ Check whether all fields in dependencies are valid. """
        for record in self:
            if not record.depends:
                continue
            for seq in record.depends.split(","):
                if not seq.strip():
                    raise UserError(_("Empty dependency in “%s”", record.depends))
                model = self.env[record.model]
                names = seq.strip().split(".")
                last = len(names) - 1
                for index, name in enumerate(names):
                    if name == 'id':
                        raise UserError(_("Compute method cannot depend on field 'id'"))
                    field = model._fields.get(name)
                    if field is None:
                        raise UserError(_(
                            'Unknown field “%(field)s” in dependency “%(dependency)s”',
                            field=name,
                            dependency=seq.strip(),
                        ))
                    if index < last and not field.relational:
                        raise UserError(_(
                            'Non-relational field “%(field)s” in dependency “%(dependency)s”',
                            field=name,
                            dependency=seq.strip(),
                        ))
                    model = model[name]