def _get_partner_phone_update(self, force_void=True):
        """Calculate if we should write the phone on the related partner. When
        the phone of the lead / partner is an empty string, we force it to False
        to not propagate a False on an empty string.

        Done in a separate method so it can be used in both ribbon and inverse
        and compute of phone update methods.

        :param bool force_void: if False, skip when lead has a void phone value.
          This is used notably to avoid propagating void lead value to a valid
          partner value.
        """
        self.ensure_one()
        if self.partner_id and (force_void or self.phone) and self.phone != self.partner_id.phone:
            lead_phone_formatted = self._phone_format(fname='phone') or self.phone or False
            partner_phone_formatted = self.partner_id._phone_format(fname='phone') or self.partner_id.phone or False
            return lead_phone_formatted != partner_phone_formatted
        return False