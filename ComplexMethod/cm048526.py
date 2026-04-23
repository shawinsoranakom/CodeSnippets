def _compute_data(self):
        for wizard in self:
            unreconciled_bank_statement_line_ids = []
            chains_to_hash = []
            if wizard.hash_date:
                for chain_info in wizard._get_chains_to_hash(wizard.company_id, wizard.hash_date):
                    if 'unreconciled' in chain_info['warnings']:
                        unreconciled_bank_statement_line_ids.extend(
                            chain_info['moves'].statement_line_ids.filtered(lambda l: not l.is_reconciled).ids
                        )
                    else:
                        chains_to_hash.append(chain_info)
            wizard.unreconciled_bank_statement_line_ids = [Command.set(unreconciled_bank_statement_line_ids)]
            wizard.chains_to_hash_with_gaps = [
                {
                    'first_move_id': chain['moves'][0].id,
                    'last_move_id': chain['moves'][-1].id,
                } for chain in chains_to_hash if 'gap' in chain['warnings']
            ]

            not_hashable_unlocked_moves = []
            move_to_hash_ids = []
            for chain in chains_to_hash:
                not_hashable_unlocked_moves.extend(chain['not_hashable_unlocked_moves'].ids)
                move_to_hash_ids.extend(chain['moves'].ids)
            wizard.not_hashable_unlocked_move_ids = [Command.set(not_hashable_unlocked_moves)]
            wizard.move_to_hash_ids = [Command.set(move_to_hash_ids)]