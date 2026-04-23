def _get_pension_fund_tax_for_line(self, element, extra_info):
        """ Apply the pension fund on all lines that have the related AliquotaIVA
            If there are AssoSoftware specific AltriDatiGestionale 'AswCassPre'
            tags that specify which lines have pension funds, only apply to them.
        """
        pension_fund_map = extra_info.get('pension_fund_taxes', {})
        tax_rate = get_float(element, './/AliquotaIVA')
        l10n_it_exemption_reason = get_text(element, "Natura")

        if not tax_rate and not l10n_it_exemption_reason:
            return None

        pension_fund_tax_candidates = pension_fund_map.get(tax_rate)
        if not pension_fund_tax_candidates:
            return None

        if l10n_it_exemption_reason and len(pension_fund_tax_candidates) > 1:
            pension_fund_tax_candidates = pension_fund_tax_candidates.filtered(lambda t: t.l10n_it_exempt_reason == l10n_it_exemption_reason)
        pension_fund_tax = pension_fund_tax_candidates[:1]

        if not pension_fund_tax:
            return None

        if not extra_info.get('pension_fund_assosoftware_tags'):
            return pension_fund_tax

        selector = ".//AltriDatiGestionali[TipoDato[contains(text(),'AswCassPre')]]/RiferimentoTesto"
        reference_text = get_text(element, selector)
        if not reference_text:
            return None

        if match := re.match(r"(?P<kind>TC\d{2}) \((?P<tax_rate>\d+)%\)", reference_text):
            rate = float(match.group("tax_rate"))
            match_kind = (match.group("kind") == pension_fund_tax.l10n_it_pension_fund_type)
            match_rate = (float_compare(rate, pension_fund_tax.amount, precision_digits=2) == 0)
            if match_kind and match_rate:
                return pension_fund_tax

        return None