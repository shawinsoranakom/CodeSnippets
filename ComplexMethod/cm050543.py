def _inverse_company_id(self):
        """
        Ensures that the new company of the project is valid for the account. If not set back the previous company, and raise a user Error.
        Ensures that the new company of the project is valid for the partner
        """
        for project in self:
            account = project.account_id
            if (
                project.partner_id
                and project.partner_id.company_id
                and project.company_id
                and project.company_id != project.partner_id.company_id
            ):
                raise UserError(_('The project and the associated partner must be linked to the same company.'))
            if not account or not account.company_id:
                continue
            # if the account of the project has more than one company linked to it, or if it has aal, do not update the account, and set back the old company on the project.
            if (account.project_count > 1 or account.line_ids) and project.company_id != account.company_id:
                raise UserError(
                    _("The project's company cannot be changed if its analytic account has analytic lines or if more than one project is linked to it."))
            account.company_id = project.company_id or project.partner_id.company_id