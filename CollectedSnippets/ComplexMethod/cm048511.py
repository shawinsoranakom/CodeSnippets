def _compute_summary_data(self):
        extra_edis = self._get_all_extra_edis()
        sending_methods = dict(self.env['res.partner']._fields['invoice_sending_method'].selection)
        sending_methods['manual'] = _('Manually')  # in batch sending, everything is done asynchronously, we never "Download"

        for wizard in self:
            edi_counter = Counter()
            sending_method_counter = Counter()

            for move in wizard.move_ids._origin:
                edi_counter += Counter([edi for edi in self._get_default_extra_edis(move)])
                sending_settings = self._get_default_sending_settings(move)
                sending_method_counter += Counter([
                    sending_method
                    for sending_method in self._get_default_sending_methods(move)
                    if self._is_applicable_to_move(sending_method, move, **sending_settings)
                ])

            summary_data = dict()
            for edi, edi_count in edi_counter.items():
                summary_data[edi] = {'count': edi_count, 'label': _("by %s", extra_edis[edi]['label'])}
            for sending_method, sending_method_count in sending_method_counter.items():
                summary_data[sending_method] = {'count': sending_method_count, 'label': sending_methods[sending_method]}

            wizard.summary_data = summary_data