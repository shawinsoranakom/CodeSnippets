def _sync_dynamic_line(self, existing_key_fname, needed_vals_fname, needed_dirty_fname, line_type, container):
        def existing():
            return {
                line: line[existing_key_fname]
                for line in container['records'].line_ids
                if line[existing_key_fname]
            }

        def needed():
            return self._sync_dynamic_line_needed_values(container['records'].mapped(needed_vals_fname))

        def dirty():
            *path, dirty_fname = needed_dirty_fname.split('.')
            eligible_recs = container['records'].mapped('.'.join(path))
            if eligible_recs._name == 'account.move.line':
                eligible_recs = eligible_recs.filtered(lambda l: l.display_type != 'cogs')
            dirty_recs = eligible_recs.filtered(dirty_fname)
            return dirty_recs, dirty_fname

        def filter_trivial(mapping):
            return {k: v for k, v in mapping.items() if 'id' not in v}

        inv_existing_before = existing()
        needed_before = needed()
        dirty_recs_before, dirty_fname = dirty()
        dirty_recs_before[dirty_fname] = False
        yield
        dirty_recs_after, dirty_fname = dirty()
        if not dirty_recs_after:  # TODO improve filter
            return
        inv_existing_after = existing()
        needed_after = needed()

        # Filter out deleted lines from `needed_before` to not recompute lines if not necessary or wanted
        line_ids = set(self.env['account.move.line'].browse(k['id'] for k in needed_before if 'id' in k).exists().ids)
        needed_before = {k: v for k, v in needed_before.items() if 'id' not in k or k['id'] in line_ids}

        # old key to new key for the same line
        before2after = {
            before: inv_existing_after[bline]
            for bline, before in inv_existing_before.items()
            if bline in inv_existing_after
        }

        if needed_after == needed_before:
            return  # do not modify user input if nothing changed in the needs
        if not needed_before and (filter_trivial(inv_existing_after) != filter_trivial(inv_existing_before)):
            return  # do not modify user input if already created manually

        existing_after = defaultdict(list)
        for k, v in inv_existing_after.items():
            existing_after[v].append(k)
        to_delete = [
            line.id
            for line, key in inv_existing_before.items()
            if key not in needed_after
            and key in existing_after
            and before2after[key] not in needed_after
        ]
        to_delete_set = set(to_delete)
        to_delete.extend(line.id
            for line, key in inv_existing_after.items()
            if key not in needed_after and line.id not in to_delete_set
        )
        to_create = {
            key: values
            for key, values in needed_after.items()
            if key not in existing_after
        }
        to_write = {
            line: values
            for key, values in needed_after.items()
            for line in existing_after[key]
            if any(
                self.env['account.move.line']._fields[fname].convert_to_write(line[fname], self)
                != values[fname]
                for fname in values
            )
        }

        while to_delete and to_create:
            key, values = to_create.popitem()
            line_id = to_delete.pop()
            self.env['account.move.line'].browse(line_id).write(
                {**key, **values, 'display_type': line_type}
            )
        if to_delete:
            self.env['account.move.line'].browse(to_delete).with_context(dynamic_unlink=True).unlink()
        if to_create:
            self.env['account.move.line'].with_context(clean_context(self.env.context)).create([
                {**key, **values, 'display_type': line_type}
                for key, values in to_create.items()
            ])
        if to_write:
            for line, values in to_write.items():
                line.write(values)