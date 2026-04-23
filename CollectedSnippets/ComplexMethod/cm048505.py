def resequence(self):
        new_values = json.loads(self.new_values)
        if self.move_ids.journal_id and self.move_ids.journal_id.restrict_mode_hash_table:
            if self.ordering == 'date':
                raise UserError(_('You can not reorder sequence by date when the journal is locked with a hash.'))
        moves_to_rename = self.env['account.move'].browse(int(k) for k in new_values.keys())
        moves_to_rename.name = False
        moves_to_rename.flush_recordset(["name"])
        # If the db is not forcibly updated, the temporary renaming could only happen in cache and still trigger the constraint

        for move_id in self.move_ids:
            if str(move_id.id) in new_values:
                if self.ordering == 'keep':
                    move_id.name = new_values[str(move_id.id)]['new_by_name']
                else:
                    move_id.name = new_values[str(move_id.id)]['new_by_date']