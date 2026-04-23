def _check_hash_integrity(self):
        """Checks that all hashed moves have still the same data as when they were hashed
        and raises an error with the result.
        """
        if not self.env.user.has_group('account.group_account_user'):
            raise UserError(_('Please contact your accountant to print the Hash integrity result.'))

        journals = self.env['account.journal'].search(self.env['account.journal']._check_company_domain(self))
        results = []

        for journal in journals:
            restricted_by_hash_table_flag = 'V' if journal.restrict_mode_hash_table else 'X'
            # We need the `sudo()` to ensure that all the moves are searched, no matter the user's access rights.
            # This is required in order to generate consistent hashes.
            # It is not an issue, since the data is only used to compute a hash and not to return the actual values.
            query = self.env['account.move'].sudo()._search(
                domain=[
                    ('journal_id', '=', journal.id),
                    ('inalterable_hash', '!=', False),
                ],
                order="secure_sequence_number ASC NULLS LAST, sequence_prefix, sequence_number ASC",
            )
            prefix2result = defaultdict(lambda: {
                'first_move': self.env['account.move'],
                'last_move': self.env['account.move'],
                'corrupted_move': self.env['account.move'],
            })
            last_move = self.env['account.move']
            self.env.execute_query(SQL("DECLARE hashed_moves CURSOR FOR %s", query.select()))
            while move_ids := self.env.execute_query(SQL("FETCH %s FROM hashed_moves", INTEGRITY_HASH_BATCH_SIZE)):
                self.env.invalidate_all()
                moves = self.env['account.move'].browse(move_id[0] for move_id in move_ids)
                if not moves and not last_move:
                    results.append({
                        'journal_name': journal.name,
                        'restricted_by_hash_table': restricted_by_hash_table_flag,
                        'status': 'no_data',
                        'msg_cover': _('There is no journal entry flagged for accounting data inalterability yet.'),
                    })
                    continue

                current_hash_version = 1
                for move in moves:
                    prefix_result = prefix2result[move.sequence_prefix]
                    if prefix_result['corrupted_move']:
                        continue
                    previous_move = prefix_result['last_move'] if not move.secure_sequence_number else last_move
                    previous_hash = previous_move.inalterable_hash or ""
                    computed_hash = move.with_context(hash_version=current_hash_version)._calculate_hashes(previous_hash)[move]
                    while move.inalterable_hash != computed_hash and current_hash_version < MAX_HASH_VERSION:
                        current_hash_version += 1
                        computed_hash = move.with_context(hash_version=current_hash_version)._calculate_hashes(previous_hash)[move]
                    if move.inalterable_hash != computed_hash:
                        prefix_result['corrupted_move'] = move
                        continue
                    if not prefix_result['first_move']:
                        prefix_result['first_move'] = move
                    prefix_result['last_move'] = move
                    last_move = move

            self.env.execute_query(SQL("CLOSE hashed_moves"))

            for prefix, prefix_result in prefix2result.items():
                if corrupted_move := prefix_result['corrupted_move']:
                    results.append({
                        'restricted_by_hash_table': restricted_by_hash_table_flag,
                        'journal_name': f"{journal.name} ({prefix}...)",
                        'status': 'corrupted',
                        'msg_cover': _(
                            "Corrupted data on journal entry with id %(id)s (%(name)s).",
                            id=corrupted_move.id,
                            name=corrupted_move.name,
                        ),
                    })
                else:
                    results.append({
                        'restricted_by_hash_table': restricted_by_hash_table_flag,
                        'journal_name': f"{journal.name} ({prefix}...)",
                        'status': 'verified',
                        'msg_cover': _("Entries are correctly hashed"),
                        'first_move_name': prefix_result['first_move'].name,
                        'first_hash': prefix_result['first_move'].inalterable_hash,
                        'first_move_date': format_date(self.env, prefix_result['first_move'].date),
                        'last_move_name': prefix_result['last_move'].name,
                        'last_hash': prefix_result['last_move'].inalterable_hash,
                        'last_move_date': format_date(self.env, prefix_result['last_move'].date),
                    })

        return {
            'results': results,
            'printing_date': format_date(self.env, fields.Date.context_today(self)),
        }