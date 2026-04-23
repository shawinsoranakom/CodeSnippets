def _l10n_it_edi_get_extra_info(self, company, document_type, body_tree, incoming=True):
        """ This function is meant to collect other information that has to be inserted on the invoice lines by submodules.
            :return: extra_info, messages_to_log
        """
        extra_info = {
            'simplified': self.env['account.move']._l10n_it_edi_is_simplified_document_type(document_type),
            'type_tax_use_domain': [('type_tax_use', '=', 'purchase' if incoming else 'sale')],
        }
        message_to_log = []
        type_tax_use_domain = extra_info['type_tax_use_domain']
        withholding_elements = body_tree.xpath('.//DatiGeneraliDocumento/DatiRitenuta')
        withholding_taxes = []
        for withholding in (withholding_elements or []):
            tipo_ritenuta = withholding.find("TipoRitenuta")
            reason = withholding.find("CausalePagamento")
            percentage = withholding.find('AliquotaRitenuta')
            withholding_type = tipo_ritenuta.text if tipo_ritenuta is not None else "RT02"
            withholding_reason = reason.text if reason is not None else "A"
            withholding_percentage = -float(percentage.text if percentage is not None else "0.0")

            if withholding_percentage == -23.0:
                prezzo_totale = 0.0
                for line in body_tree.xpath('.//DettaglioLinee'):
                    prezzo_totale += get_float(line, './/PrezzoTotale')
                importo_ritenuta = get_float(withholding, './/ImportoRitenuta')
                withholding_percentage = -float_round((importo_ritenuta / prezzo_totale) * 100, 1)

            # Some bills involving ENASARCO come in with a wrong withholding_reason
            # so we defend ourselves by searching with exact type and reason first,
            # then with just the type
            for extra_domain, message in ([(
                [
                    ('l10n_it_withholding_type', '=', withholding_type),
                    ('l10n_it_withholding_reason', '=', withholding_reason),
                    *type_tax_use_domain
                ],
                None
            ), (
                [
                    ('l10n_it_withholding_type', '=', withholding_type),
                    *type_tax_use_domain
                ],
                _("ENASARCO tax (type %(wtype)s) has wrong reason %(reason)s",
                  wtype=withholding_type, reason=withholding_reason))
            ]):
                if withholding_tax := self._l10n_it_edi_search_tax_for_import(
                    company, withholding_percentage, extra_domain,
                ):
                    withholding_taxes.append(withholding_tax)
                    break
            else:
                message = _("Withholding tax not found")
            if message:
                message_to_log.append(Markup("%s<br/>%s") % (message, self._compose_info_message(body_tree, '.')))

        extra_info["withholding_taxes"] = withholding_taxes

        pension_fund_elements = body_tree.xpath('.//DatiGeneraliDocumento/DatiCassaPrevidenziale')
        pension_fund_taxes = {}
        for pension_fund in (pension_fund_elements or []):
            pension_fund_type = pension_fund.find("TipoCassa")
            tax_factor_percent = pension_fund.find("AlCassa")
            vat_tax_factor_percent = pension_fund.find("AliquotaIVA")
            pension_fund_type = pension_fund_type.text if pension_fund_type is not None else ""
            tax_factor_percent = float(tax_factor_percent.text or "0.0")
            vat_tax_factor_percent = float(vat_tax_factor_percent.text or "0.0")
            pension_fund_tax = self._l10n_it_edi_search_tax_for_import(
                company,
                tax_factor_percent,
                ([('l10n_it_pension_fund_type', '=', pension_fund_type)]
                 + type_tax_use_domain))
            if pension_fund_tax:
                if vat_tax_factor_percent not in pension_fund_taxes:
                    pension_fund_taxes[vat_tax_factor_percent] = pension_fund_tax
                else:
                    pension_fund_taxes[vat_tax_factor_percent] |= pension_fund_tax
            else:
                message_to_log.append(Markup("%s<br/>%s") % (
                    _("Pension Fund tax not found"),
                    self.env['account.move']._compose_info_message(body_tree, '.'),
                ))
        extra_info["pension_fund_taxes"] = pension_fund_taxes

        # If the AssoSoftware specs are used on the invoice, then only apply
        # the Pension Fund tax to the lines that show an AswCassPre
        # additional tag (AltriDatiGestionali)
        selector = ".//AltriDatiGestionali/TipoDato[contains(text(), 'AswCassPre')]"
        if get_text(body_tree, selector):
            extra_info["pension_fund_assosoftware_tags"] = True
        return extra_info, message_to_log