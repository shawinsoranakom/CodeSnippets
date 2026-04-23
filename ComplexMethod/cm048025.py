def _compute_peppol_parent_company_id(self):
        self.peppol_parent_company_id = False
        for company in self:
            for parent_company in company.parent_ids[::-1][1:]:
                if (
                    company.peppol_eas
                    and company.peppol_endpoint
                    and company.peppol_eas == parent_company.peppol_eas
                    and company.peppol_endpoint == parent_company.peppol_endpoint
                ) or (
                    not company.peppol_endpoint
                    and parent_company.peppol_eas
                    and parent_company.peppol_endpoint
                ):
                    company.peppol_parent_company_id = parent_company
                    break