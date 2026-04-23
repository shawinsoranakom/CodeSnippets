def _find_sms_sms(self, partner, number, status, content=None):
        if number is None and partner:
            number = partner._phone_format()
        domain = [('id', 'in', self._new_sms.ids),
                  ('partner_id', '=', partner.id),
                  ('number', '=', number)]
        if status:
            domain += [('state', '=', status)]

        sms = self.env['sms.sms'].sudo().search(domain)
        if len(sms) > 1 and content:
            sms = sms.filtered(lambda s: content in (s.body or ""))
        if not sms:
            debug_info = '\n'.join(
                f"To {sms.number} ({sms.partner_id}) / state {sms.state}"
                for sms in self._new_sms
            )
            raise AssertionError(
                f'sms.sms not found for {partner} (number: {number} / status {status})\n--MOCKED DATA\n{debug_info}'
            )
        if len(sms) > 1:
            raise NotImplementedError(
                f'Found {len(sms)} sms.sms for {partner} (number: {number} / status {status})'
            )
        return sms