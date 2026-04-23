def _create_document_from_attachment(self, attachment_ids):
        """ Create the invoices from files."""
        if not self:
            self = self.env['account.journal'].browse(self.env.context.get("default_journal_id"))  # noqa: PLW0642
        move_type = self.env.context.get("default_move_type", "entry")
        if not self:
            if move_type in self.env['account.move'].get_sale_types(include_receipts=True):
                journal_type = "sale"
            elif move_type in self.env['account.move'].get_purchase_types(include_receipts=True):
                journal_type = "purchase"
            else:
                raise UserError(_("The journal in which to upload the invoice is not specified. "))
            self = self.env['account.journal'].search([  # noqa: PLW0642
                *self.env['account.journal']._check_company_domain(self.env.company),
                ('type', '=', journal_type),
            ], limit=1)

        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            raise UserError(_("No attachment was provided"))

        if not self:
            raise UserError(self.env['account.journal']._build_no_journal_error_msg(self.env.company.display_name, [journal_type]))

        # Create one invoice per group.
        invoices = self.env['account.move'] \
            .with_context(
                default_journal_id=self.id,
                skip_is_manually_modified=True,
            ) \
            ._create_records_from_attachments(attachments)

        for invoice in invoices:
            invoice._autopost_bill()

        return invoices