def get_panel_data(self):
        self.ensure_one()
        if not self.env.user.has_group('project.group_project_user'):
            return {}
        show_profitability = self._show_profitability()
        panel_data = {
            'user': self._get_user_values(),
            'buttons': sorted(self._get_stat_buttons(), key=lambda k: k['sequence']),
            'currency_id': self.currency_id.id,
            'show_project_profitability_helper': show_profitability and self._show_profitability_helper(),
            'show_milestones': self.allow_milestones,
        }
        if self.allow_milestones:
            panel_data['milestones'] = self._get_milestones()
        if show_profitability:
            profitability_items = self.with_context(active_test=False)._get_profitability_items()
            if self._get_profitability_sequence_per_invoice_type() and profitability_items and 'revenues' in profitability_items and 'costs' in profitability_items:  # sort the data values
                profitability_items['revenues']['data'] = sorted(profitability_items['revenues']['data'], key=lambda k: k['sequence'])
                profitability_items['costs']['data'] = sorted(profitability_items['costs']['data'], key=lambda k: k['sequence'])
            panel_data['profitability_items'] = profitability_items
            panel_data['profitability_labels'] = self._get_profitability_labels()
        return panel_data