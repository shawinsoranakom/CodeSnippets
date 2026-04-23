def _match_address(self, partner):
        self.ensure_one()
        if self.country_ids and partner.country_id not in self.country_ids:
            return False
        if self.state_ids and partner.state_id not in self.state_ids:
            return False
        if self.zip_prefix_ids:
            regex = re.compile('|'.join(['^' + zip_prefix for zip_prefix in self.zip_prefix_ids.mapped('name')]))
            if not partner.zip or not re.match(regex, partner.zip.upper()):
                return False
        return True