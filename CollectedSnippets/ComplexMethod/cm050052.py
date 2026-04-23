def _get_tax_category_code(self, customer, supplier, tax):
        """
        Predicts the tax category code for a tax applied to a given base line.
        If the tax has a defined category code, it is returned.
        Otherwise, a reasonable default is provided, though it may not always be accurate.

        Source: doc of Peppol (but the CEF norm is also used by factur-x, yet not detailed)
        https://docs.peppol.eu/poacc/billing/3.0/syntax/ubl-invoice/cac-TaxTotal/cac-TaxSubtotal/cac-TaxCategory/cbc-TaxExemptionReasonCode/
        https://docs.peppol.eu/poacc/billing/3.0/codelist/vatex/
        https://docs.peppol.eu/poacc/billing/3.0/codelist/UNCL5305/
        """
        # add Norway, Iceland, Liechtenstein
        if not tax:
            return 'E'

        if tax.ubl_cii_tax_category_code:
            return tax.ubl_cii_tax_category_code

        if customer.country_id.code == 'ES' and customer.zip:
            if customer.zip[:2] in ('35', '38'):  # Canary
                # [BR-IG-10]-A VAT breakdown (BG-23) with VAT Category code (BT-118) "IGIC" shall not have a VAT
                # exemption reason code (BT-121) or VAT exemption reason text (BT-120).
                return 'L'
            if customer.zip[:2] in ('51', '52'):
                return 'M'  # Ceuta & Mellila

        if supplier.country_id == customer.country_id:
            if not tax or tax.amount == 0:
                # in theory, you should indicate the precise law article
                return 'E'
            elif tax.has_negative_factor:
                # Special case: Purchase reverse-charge taxes for self-billed invoices.
                # From the buyer's perspective, this is a standard tax with a non-zero percentage but
                # two tax repartition lines that cancel each other out.
                # But from the seller's perspective, this is a zero-percent tax (VAT liability is deferred
                # to the buyer).
                # For a self-billed invoice we, the buyer, create the invoice on behalf of the seller.
                # So in the XML we put the zero-percent tax with code 'AE' that the seller would have used.
                return 'AE'
            else:
                return 'S'  # standard VAT

        if supplier.country_id.code in EUROPEAN_ECONOMIC_AREA_COUNTRY_CODES and supplier.vat:
            if tax.amount != 0 and not tax.has_negative_factor:
                # Special case: Purchase reverse-charge taxes for self-billed invoices.
                # See explanation above.
                # In the XML we put the zero-percent tax with code 'G' or 'K' that the buyer would have used.
                return 'S'
            if customer.country_id.code not in EUROPEAN_ECONOMIC_AREA_COUNTRY_CODES:
                return 'G'
            if customer.country_id.code in EUROPEAN_ECONOMIC_AREA_COUNTRY_CODES:
                return 'K'

        if tax.amount != 0:
            return 'S'
        else:
            return 'E'