def _invoice_constraints_cen_en16931_ubl(self, invoice, vals):
        """
        corresponds to the errors raised by ' schematron/openpeppol/3.13.0/xslt/CEN-EN16931-UBL.xslt' for invoices.
        This xslt was obtained by transforming the corresponding sch
        https://docs.peppol.eu/poacc/billing/3.0/files/CEN-EN16931-UBL.sch.
        """
        eu_countries = self.env.ref('base.europe').country_ids
        intracom_delivery = (vals['customer'].country_id in eu_countries
                             and vals['supplier'].country_id in eu_countries
                             and vals['customer'].country_id != vals['supplier'].country_id)

        nsmap = self._get_document_nsmap(vals)

        constraints = {
            # [BR-IC-12]-In an Invoice with a VAT breakdown (BG-23) where the VAT category code (BT-118) is
            # "Intra-community supply" the Deliver to country code (BT-80) shall not be blank.
            'cen_en16931_delivery_country_code': (
                _("For intracommunity supply, the delivery address should be included.")
            ) if intracom_delivery and dict_to_xml(vals['document_node']['cac:Delivery']['cac:DeliveryLocation'], nsmap=nsmap, tag='cac:DeliveryLocation') is None else None,

            # [BR-IC-11]-In an Invoice with a VAT breakdown (BG-23) where the VAT category code (BT-118) is
            # "Intra-community supply" the Actual delivery date (BT-72) or the Invoicing period (BG-14)
            # shall not be blank.
            'cen_en16931_delivery_date_invoicing_period': (
                _("For intracommunity supply, the actual delivery date or the invoicing period should be included.")
                if (
                    intracom_delivery
                    and dict_to_xml(vals['document_node']['cac:Delivery']['cbc:ActualDeliveryDate'], nsmap=nsmap, tag='cbc:ActualDeliveryDate') is None
                    and dict_to_xml(vals['document_node']['cac:InvoicePeriod'], nsmap=nsmap, tag='cac:InvoicePeriod') is None
                )
                else None
            )
        }

        # [BR-61]-If the Payment means type code (BT-81) means SEPA credit transfer, Local credit transfer or
        # Non-SEPA international credit transfer, the Payment account identifier (BT-84) shall be present.
        # note: Payment account identifier is <cac:PayeeFinancialAccount>
        # note: no need to check account_number, because it's a required field for a partner_bank
        for node in vals['document_node']['cac:PaymentMeans']:
            if node['cbc:PaymentMeansCode']['_text'] in (30, 58):
                constraints['cen_en16931_payment_account_identifier'] = self._check_required_fields(invoice, 'partner_bank_id')

        line_tag = self._get_tags_for_document_type(vals)['document_line']
        line_nodes = vals['document_node'][line_tag]

        for line_node in line_nodes:
            if not (line_node['cac:Item']['cbc:Name'] or {}).get('_text'):
                # [BR-25]-Each Invoice line (BG-25) shall contain the Item name (BT-153).
                constraints.update({'cen_en16931_item_name': _("Each invoice line should have a product or a label.")})
                break

            if len(line_node['cac:Item']['cac:ClassifiedTaxCategory']) != 1:
                # [UBL-SR-48]-Invoice lines shall have one and only one classified tax category.
                # /!\ exception: possible to have any number of ecotaxes (fixed tax) with a regular percentage tax
                constraints['cen_en16931_tax_line'] = _("Each invoice line shall have one and only one tax.")

        for role in ('supplier', 'customer'):
            party_node = vals['document_node']['cac:AccountingCustomerParty'] if role == 'customer' else vals['document_node']['cac:AccountingSupplierParty']
            constraints[f'cen_en16931_{role}_country'] = (
                _("The country is required for the %s.", role)
                if not party_node['cac:Party']['cac:PostalAddress']['cac:Country']['cbc:IdentificationCode']['_text']
                else None
            )
            tax_scheme_node = party_node['cac:Party']['cac:PartyTaxScheme']
            if tax_scheme_node and (
                self._name in ('account.edi.xml.ubl_bis3', 'account.edi.xml.ubl_nl', 'account.edi.xml.ubl_de')
                and (tax_scheme_node[0]['cac:TaxScheme']['cbc:ID']['_text'] == 'VAT')
                and not (tax_scheme_node[0]['cbc:CompanyID']['_text'][:2].isalpha())
            ):
                # [BR-CO-09]-The Seller VAT identifier (BT-31), the Seller tax representative VAT identifier (BT-63)
                # and the Buyer VAT identifier (BT-48) shall have a prefix in accordance with ISO code ISO 3166-1
                # alpha-2 by which the country of issue may be identified. Nevertheless, Greece may use the prefix 'EL'.
                constraints.update({f'cen_en16931_{role}_vat_country_code': _(
                    "The VAT of the %s should be prefixed with its country code.", role)})

        if invoice.partner_shipping_id:
            # [BR-57]-Each Deliver to address (BG-15) shall contain a Deliver to country code (BT-80).
            constraints['cen_en16931_delivery_address'] = self._check_required_fields(invoice.partner_shipping_id, 'country_id')
        return constraints