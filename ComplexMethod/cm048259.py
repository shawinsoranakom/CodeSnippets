def _compute_company_informations(self):
        informations = '%s\n' % self.company_id.street if self.company_id.street else ''
        informations += '%s\n' % self.company_id.street2 if self.company_id.street2 else ''
        informations += '%s' % self.company_id.zip if self.company_id.zip else ''
        informations += '\n' if self.company_id.zip and not self.company_id.city else ''
        informations += ' - ' if self.company_id.zip and self.company_id.city else ''
        informations += '%s\n' % self.company_id.city if self.company_id.city else ''
        informations += '%s\n' % self.company_id.state_id.display_name if self.company_id.state_id else ''
        informations += '%s' % self.company_id.country_id.display_name if self.company_id.country_id else ''
        vat_display = self.company_id.country_id.vat_label or _('VAT')
        vat_display = '\n' + vat_display + ': '
        informations += '%s %s' % (vat_display, self.company_id.vat) if self.company_id.vat else ''

        for record in self:
            record.company_informations = informations