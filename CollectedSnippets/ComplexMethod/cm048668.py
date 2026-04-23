def _get_chain_info(self, force_hash=False, include_pre_last_hash=False, early_stop=False):
        """All records in `self` must belong to the same journal and sequence_prefix
        """
        if not self:
            return False

        # Delegate to the database, instead of max(self, key=lambda m: m.sequence_number)
        last_move_in_chain = (
            self.env['account.move']
            .sudo()
            .search_fetch(
                domain=[('id', 'in', self.ids)],
                field_names=[
                    'sequence_prefix',
                    'sequence_number',
                    'journal_id',
                    # Pre-emptive fetching for `_is_move_restricted`
                    'state',
                    'restrict_mode_hash_table',
                ],
                order='sequence_number desc',
                limit=1,
            )
        )
        journal = last_move_in_chain.journal_id
        if not self._is_move_restricted(last_move_in_chain, force_hash=force_hash):
            return False

        common_domain = [
            ('journal_id', '=', journal.id),
            ('sequence_prefix', '=', last_move_in_chain.sequence_prefix),
        ]
        last_move_hashed = self.env['account.move'].search_fetch([
            *common_domain,
            ('inalterable_hash', '!=', False),
        ], ['sequence_number', 'inalterable_hash'], order='sequence_number desc', limit=1)

        domain = self.env['account.move']._get_move_hash_domain([
            *common_domain,
            ('sequence_number', '<=', last_move_in_chain.sequence_number),
            ('inalterable_hash', '=', False),
        ], force_hash=True)
        if last_move_hashed and not include_pre_last_hash:
            # Hash moves only after the last hashed move, not the ones that may have been posted before the journal was set on restrict mode
            domain &= Domain('sequence_number', '>', last_move_hashed.sequence_number)

        # On the accounting dashboard, we are only interested on whether there are documents to hash or not
        # so we can stop the computation early if we find at least one document to hash
        if early_stop:
            return self.env['account.move'].sudo().search_count(domain, limit=1)
        moves_to_hash = self.env['account.move'].sudo().search_fetch(domain, ['sequence_number'], order='sequence_number')
        info = {
            'previous_hash': last_move_hashed.inalterable_hash,
            'last_move_hashed': last_move_hashed,
        }
        if self.env.context.get('chain_info_warnings', True):
            warnings = set()
            if moves_to_hash:
                # gap warning
                if last_move_hashed:
                    first = last_move_hashed.sequence_number
                    difference = len(moves_to_hash)
                else:
                    first = moves_to_hash[0].sequence_number
                    difference = len(moves_to_hash) - 1
                last = moves_to_hash[-1].sequence_number
                if first + difference != last:
                    warnings.add('gap')

                # unreconciled warning
                has_unreconciled = bool(self.env['account.bank.statement.line'].search_count([
                    ('move_id', 'in', moves_to_hash.ids),
                    ('is_reconciled', '=', False),
                ], limit=1))
                if has_unreconciled:
                    warnings.add('unreconciled')
            else:
                warnings.add('no_document')

            info['warnings'] = warnings

        moves = moves_to_hash.sudo(False)
        info.update({
            'moves': moves,
            'remaining_moves': self - moves,
        })
        return info