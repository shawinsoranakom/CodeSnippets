def _compute_application_count(self):
        """
        This method will calculate the number of applications that are either
        directly or indirectly linked to the current application(s)
        - An application is considered directly linked if it shares the same
          pool_applicant_id
        - An application is considered indirectly_linked if it has the same
          value as the current application(s) in any of the following field:
          email, phone number or linkedin

        Note: If self has pool_applicant_id, email, phone number or linkedin set
        this method will include self in the returned count
        """
        domain = self._get_similar_applicants_domain(ignore_talent=True)
        matching_applicants = self.env["hr.applicant"].with_context(active_test=False).search(domain)

        email_map = defaultdict(set)
        phone_map = defaultdict(set)
        linkedin_map = defaultdict(set)
        pool_applicant_map = defaultdict(set)
        for app in matching_applicants:
            if app.email_normalized:
                email_map[app.email_normalized].add(app.id)
            if app.partner_phone_sanitized:
                phone_map[app.partner_phone_sanitized].add(app.id)
            if app.linkedin_profile:
                linkedin_map[app.linkedin_profile].add(app.id)
            if app.pool_applicant_id:
                pool_applicant_map[app.pool_applicant_id].add(app.id)

        for applicant in self:
            related_ids = set()
            if applicant.email_normalized:
                related_ids.update(email_map.get(applicant.email_normalized, set()))
            if applicant.partner_phone_sanitized:
                related_ids.update(phone_map.get(applicant.partner_phone_sanitized, set()))
            if applicant.linkedin_profile:
                related_ids.update(linkedin_map.get(applicant.linkedin_profile, set()))
            if applicant.pool_applicant_id:
                related_ids.update(pool_applicant_map.get(applicant.pool_applicant_id, set()))

            count = len(related_ids)

            applicant.application_count = max(0, count)