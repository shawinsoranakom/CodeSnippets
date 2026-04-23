def _compute_statistics(self):
        """ Compute statistics of the mass mailing """
        for key in (
            'scheduled', 'expected', 'canceled', 'sent', 'pending', 'delivered', 'opened',
            'process', 'clicked', 'replied', 'bounced', 'failed', 'received_ratio',
            'opened_ratio', 'replied_ratio', 'bounced_ratio',
        ):
            self[key] = False

        result = self.env["mailing.trace"].sudo()._read_group(
            [("mass_mailing_id", "in", self.ids)],
            ['mass_mailing_id', 'trace_status'],
            ['__count', 'links_click_datetime:count', 'sent_datetime:count'])

        result_per_mailing = defaultdict(lambda: defaultdict(int))
        for mailing, trace_status, count, links_click_datetime, sent_datetime in result:
            result_per_mailing[mailing][trace_status] = count
            result_per_mailing[mailing]['links_click_datetime'] += links_click_datetime
            result_per_mailing[mailing]['sent_datetime'] += sent_datetime

        for mailing in self:
            line = result_per_mailing[mailing]
            values = {
                'scheduled': line['outgoing'],
                'expected': sum(v for k, v in line.items() if k not in ('links_click_datetime', 'sent_datetime')),
                'canceled': line['cancel'],
                'pending': line['pending'],
                'delivered': line['sent'] + line['open'] + line['reply'],
                'opened': line['open'] + line['reply'],
                'replied': line['reply'],
                'bounced': line['bounce'],
                'failed': line['error'],
                'clicked': line['links_click_datetime'],
                'sent': line['sent_datetime'],
            }
            total = (values['expected'] - values['canceled']) or 1
            total_no_error = (values['expected'] - values['canceled'] - values['bounced'] - values['failed']) or 1
            total_sent = (values['expected'] - values['canceled'] - values['failed']) or 1
            values['received_ratio'] = float_round(100.0 * values['delivered'] / total, precision_digits=2)
            values['opened_ratio'] = float_round(100.0 * values['opened'] / total_no_error, precision_digits=2)
            values['replied_ratio'] = float_round(100.0 * values['replied'] / total_no_error, precision_digits=2)
            values['bounced_ratio'] = float_round(100.0 * values['bounced'] / total_sent, precision_digits=2)
            mailing.update(values)