def _compute_warnings(self):
        for wizard in self:
            warnings = {}

            if not wizard.hash_date:
                wizard.warnings = warnings
                continue

            if wizard.unreconciled_bank_statement_line_ids:
                ignored_sequence_prefixes = list(set(wizard.unreconciled_bank_statement_line_ids.move_id.mapped('sequence_prefix')))
                warnings['account_unreconciled_bank_statement_line_ids'] = {
                    'message': _("There are still unreconciled bank statement lines before the selected date. "
                                 "The entries from journal prefixes containing them will not be secured: %(prefix_info)s",
                                 prefix_info=ignored_sequence_prefixes),
                    'level': 'danger',
                    'action_text': _("Review Statements"),
                    'action': wizard.company_id._get_unreconciled_statement_lines_redirect_action(wizard.unreconciled_bank_statement_line_ids),
                }

            draft_entries = self.env['account.move'].search_count(
                wizard._get_draft_moves_in_hashed_period_domain(),
                limit=1
            )
            if draft_entries:
                warnings['account_unhashed_draft_entries'] = {
                    'message': _("There are still draft entries before the selected date."),
                    'action_text': _("Review Entries"),
                    'action': wizard.action_show_draft_moves_in_hashed_period(),
                }

            not_hashable_unlocked_moves = wizard.not_hashable_unlocked_move_ids
            if not_hashable_unlocked_moves:
                warnings['account_not_hashable_unlocked_moves'] = {
                    'message': _("There are entries that cannot be hashed. They can be protected by the Hard Lock Date."),
                    'action_text': _("Review Entries"),
                    'action': wizard.action_show_moves(not_hashable_unlocked_moves),
                }

            if wizard.chains_to_hash_with_gaps:
                OR_domains = []
                for chain in wizard.chains_to_hash_with_gaps:
                    first_move = self.env['account.move'].browse(chain['first_move_id'])
                    last_move = self.env['account.move'].browse(chain['last_move_id'])
                    OR_domains.append([
                        *self.env['account.move']._check_company_domain(wizard.company_id),
                        ('journal_id', '=', last_move.journal_id.id),
                        ('sequence_prefix', '=', last_move.sequence_prefix),
                        ('sequence_number', '<=', last_move.sequence_number),
                        ('sequence_number', '>=', first_move.sequence_number),
                    ])
                domain = Domain.OR(OR_domains)
                warnings['account_sequence_gap'] = {
                    'message': _("Securing these entries will create at least one gap in the sequence."),
                    'action_text': _("Review Entries"),
                    'action': {
                        **self.env['account.journal']._show_sequence_holes(list(domain)),
                        'views': [[self.env.ref('account.view_move_tree_multi_edit').id, 'list'], [self.env.ref('account.view_move_form').id, 'form']],
                    }
                }

            moves_to_hash_after_selected_date = wizard.move_to_hash_ids.filtered(lambda move: move.date > wizard.hash_date)
            if moves_to_hash_after_selected_date:
                warnings['account_move_to_secure_after_selected_date'] = {
                    'message': _("Securing these entries will also secure entries after the selected date."),
                    'action_text': _("Review Entries"),
                    'action': wizard.action_show_moves(moves_to_hash_after_selected_date),
                }

            wizard.warnings = warnings