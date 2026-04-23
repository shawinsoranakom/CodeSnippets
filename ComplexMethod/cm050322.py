def _l10n_it_edi_services_or_goods(self):
        """
            Services and goods have different tax grids when VAT is Reverse Charged, and they can't
            be mixed in the same invoice, because the TipoDocumento depends on which which kind
            of product is bought and it's unambiguous.
        """
        self.ensure_one()
        scopes = []
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_subsection', 'line_note')):
            tax_ids_with_tax_scope = line.tax_ids.filtered(lambda x: x.tax_scope)
            if tax_ids_with_tax_scope:
                scopes += tax_ids_with_tax_scope.mapped('tax_scope')
            else:
                scopes.append(line.product_id and line.product_id.type == 'service' and 'service' or 'consu')

        if set(scopes) == {'consu', 'service'}:
            return "both"
        return scopes and scopes.pop()