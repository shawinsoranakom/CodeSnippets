def write(self, vals):
        protected_fields = ('type', 'l10n_ar_afip_pos_system', 'l10n_ar_afip_pos_number', 'l10n_latam_use_documents')
        fields_to_check = [field for field in protected_fields if field in vals]

        if fields_to_check:
            self.env.cr.execute("SELECT DISTINCT(journal_id) FROM account_move WHERE posted_before = True")
            res = self.env.cr.fetchall()
            journal_with_entry_ids = [journal_id for journal_id, in res]

            for journal in self:
                if (
                    journal.company_id.account_fiscal_country_id.code != "AR"
                    or journal.type not in ['sale', 'purchase']
                    or journal.id not in journal_with_entry_ids
                ):
                    continue

                for field in fields_to_check:
                    # Wouldn't work if there was a relational field, as we would compare an id with a recordset.
                    if vals[field] != journal[field]:
                        raise UserError(_("You can not change %s journal's configuration if it already has validated invoices", journal.name))

        return super().write(vals)