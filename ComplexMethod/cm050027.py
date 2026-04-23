def _get_similar_applicants_domain(self, ignore_talent=False, only_talent=False):
        """
        This method returns a domain for the applicants whitch match with the
        current applicant according to email_from, partner_phone or linkedin_profile.
        Thus, search on the domain will return the current applicant as well
        if any of the following fields are filled.

        Args:
            ignore_talent: if you want the domain to only include applicants not belonging to a talent pool
            only_talent: if you want the domain to only include applicants belonging to a talent pool

        Returns:
            Domain()
        """
        domain = Domain.OR([
            Domain("id", "in", self.ids),
            Domain("email_normalized", "in", [email for email in self.mapped("email_normalized") if email]),
            Domain("partner_phone_sanitized", "in", [phone for phone in self.mapped("partner_phone_sanitized") if phone]),
            Domain("linkedin_profile", "in", [linkedin_profile for linkedin_profile in self.mapped("linkedin_profile") if linkedin_profile]),
            Domain("pool_applicant_id", "in", [pool_applicant.id for pool_applicant in self.mapped("pool_applicant_id") if pool_applicant]),
        ])
        if ignore_talent:
            domain &= Domain("talent_pool_ids", "=", False)
        if only_talent:
            domain &= Domain("talent_pool_ids", "!=", False)
        return domain