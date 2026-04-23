def _modified_triggers(self, tree: TriggerTree, create: bool = False) -> Iterable[tuple[Field, BaseModel, bool]]:
        """ Return an iterator traversing a tree of field triggers on ``self``,
        traversing backwards field dependencies along the way, and yielding
        tuple ``(field, records, created)`` to recompute.
        """
        if not self:
            return

        # first yield what to compute
        for field in tree.root:
            yield field, self, create

        # then traverse dependencies backwards, and proceed recursively
        for field, subtree in tree.items():
            if create and field.type in ('many2one', 'many2one_reference'):
                # upon creation, no other record has a reference to self
                continue

            # subtree is another tree of dependencies
            model = self.env[field.model_name]
            for invf in model.pool.field_inverses[field]:
                # use an inverse of field without domain
                if not (invf.type in ('one2many', 'many2many') and invf.domain):
                    if invf.type == 'many2one_reference':
                        rec_ids = OrderedSet()
                        for rec in self:
                            try:
                                if rec[invf.model_field] == field.model_name:
                                    rec_ids.add(rec[invf.name])
                            except MissingError:
                                continue
                        records = model.browse(rec_ids)
                    else:
                        try:
                            records = self[invf.name]
                        except MissingError:
                            records = self.exists()[invf.name]

                    # TODO: find a better fix
                    if field.model_name == records._name:
                        if not any(self._ids):
                            # if self are new, records should be new as well
                            records = records.browse(it and NewId(it) for it in records._ids)
                        break
            else:
                new_records = self.filtered(lambda r: not r.id)
                real_records = self - new_records
                records = model.browse()
                if real_records:
                    records = model.search([(field.name, 'in', real_records.ids)], order='id')
                if new_records:
                    field_cache = field._get_cache(model.env)
                    cache_records = model.browse(field_cache)
                    new_ids = set(self._ids)
                    records |= cache_records.filtered(lambda r: not set(r[field.name]._ids).isdisjoint(new_ids))

            yield from records._modified_triggers(subtree)