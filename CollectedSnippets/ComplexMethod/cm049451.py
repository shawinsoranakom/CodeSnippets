def _inverse_l10n_latam_document_number(self):
        """Inherit to complete the l10n_latam_document_number with the expected 8 characters after that a '-'

        After formatting the document number with zfill(8), the name field is also synchronized
        to ensure both fields remain consistent.

        Example: Change F01-32 by F01-00000032, to avoid incorrect values on the reports
        """
        super()._inverse_l10n_latam_document_number()
        to_review = self.filtered(
            lambda x: x.journal_id.type == "purchase"
            and x.l10n_latam_document_type_id
            and x.l10n_latam_document_type_id.code in ("01", "03", "07", "08")
            and x.l10n_latam_document_number
            and "-" in x.l10n_latam_document_number
            and x.l10n_latam_document_type_id.country_id.code == "PE"
        )
        for rec in to_review:
            number = rec.l10n_latam_document_number.split("-")
            rec.l10n_latam_document_number = "%s-%s" % (number[0], number[1].zfill(8))

            # Synchronize the name field with the formatted document number
            # to ensure consistency between l10n_latam_document_number and name fields
            expected_name = (
                f"{rec.l10n_latam_document_type_id.doc_code_prefix} "
                f"{rec.l10n_latam_document_number}"
            )
            if rec.name != expected_name:
                rec.name = expected_name