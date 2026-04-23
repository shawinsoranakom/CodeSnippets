def _compute_talent_pool_count(self):
        """
        This method will find the amount of talent pools the current application is associated with.
        An application can either be associated directly with a talent pool through talent_pool_ids
        and/or pool_applicant_id.talent_pool_ids or indirectly by having the same email, phone
        number or linkedin as a directly linked application.
        """
        pool_applicants = self.filtered("is_applicant_in_pool")
        (self - pool_applicants).talent_pool_count = 0

        if not pool_applicants:
            return

        directly_linked = pool_applicants.filtered("pool_applicant_id")
        for applicant in directly_linked:
            # All talents(applications with talent_pool_ids set) have a pool_applicant_id set to
            # themselves which is the reason we only look for that instead of searching for all
            # applications with talent_pool_ids and all applications with pool_applicant_id seperately
            applicant.talent_pool_count = len(applicant.pool_applicant_id.talent_pool_ids)

        indirectly_linked = pool_applicants - directly_linked
        if not indirectly_linked:
            return

        all_emails = {a.email_normalized for a in indirectly_linked if a.email_normalized}
        all_phones = {a.partner_phone_sanitized for a in indirectly_linked if a.partner_phone_sanitized}
        all_linkedins = {a.linkedin_profile for a in indirectly_linked if a.linkedin_profile}

        epl_domain = Domain.FALSE
        if all_emails:
            epl_domain |= Domain("email_normalized", "in", list(all_emails))
        if all_phones:
            epl_domain |= Domain("partner_phone_sanitized", "in", list(all_phones))
        if all_linkedins:
            epl_domain |= Domain("linkedin_profile", "in", list(all_linkedins))

        pool_domain = Domain(["|", ("talent_pool_ids", "!=", False), ("pool_applicant_id", "!=", False)])
        domain = pool_domain & epl_domain
        in_pool_applicants = self.env["hr.applicant"].with_context(active_test=True).search(domain)

        in_pool_emails = defaultdict(int)
        in_pool_phones = defaultdict(int)
        in_pool_linkedins = defaultdict(int)

        for applicant in in_pool_applicants:
            talent_pool_count = len(applicant.pool_applicant_id.talent_pool_ids)
            if applicant.email_normalized:
                in_pool_emails[applicant.email_normalized] = talent_pool_count
            if applicant.partner_phone_sanitized:
                in_pool_phones[applicant.partner_phone_sanitized] = talent_pool_count
            if applicant.linkedin_profile:
                in_pool_linkedins[applicant.linkedin_profile] = talent_pool_count

        for applicant in indirectly_linked:
            if applicant.email_from and in_pool_emails[applicant.email_normalized]:
                applicant.talent_pool_count = in_pool_emails[applicant.email_normalized]
            elif applicant.partner_phone_sanitized and in_pool_phones[applicant.partner_phone_sanitized]:
                applicant.talent_pool_count = in_pool_phones[applicant.partner_phone_sanitized]
            elif applicant.linkedin_profile and in_pool_linkedins[applicant.linkedin_profile]:
                applicant.talent_pool_count = in_pool_linkedins[applicant.linkedin_profile]
            else:
                applicant.talent_pool_count = 0