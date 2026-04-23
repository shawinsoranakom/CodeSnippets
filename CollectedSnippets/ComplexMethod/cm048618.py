def _get_fpos_validation_functions(self, partner):
        """ Returns a list of functions to validate fiscal positions against a partner.
        """
        return [
            # vat required
            lambda fpos: (
                not fpos.vat_required or partner._get_vat_required_valid(company=self.env.company)
            ),
            # zip code
            lambda fpos:(
                not (fpos.zip_from and fpos.zip_to)
                or (partner.zip and (fpos.zip_from <= partner.zip <= fpos.zip_to))
            ),
            # state
            lambda fpos: (
                not fpos.state_ids
                or (partner.state_id in fpos.state_ids)
            ),
            # country
            lambda fpos: (
                not fpos.country_id
                or (partner.country_id == fpos.country_id)
            ),
            # country group
            lambda fpos: (
                not fpos.country_group_id
                or (partner.country_id in fpos.country_group_id.country_ids and
                    (not partner.state_id or partner.state_id not in fpos.country_group_id.exclude_state_ids))
            ),
        ]