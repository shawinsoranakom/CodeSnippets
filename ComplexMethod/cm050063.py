def _ubl_get_delivery_node_from_delivery_address(self, vals):
        # EXTENDS account.edi.ubl
        node = super()._ubl_get_delivery_node_from_delivery_address(vals)
        invoice = vals.get('invoice')
        if not invoice:
            return node

        if invoice.delivery_date:
            node['cbc:ActualDeliveryDate']['_text'] = invoice.delivery_date

        # Intracom delivery inside European area.
        customer = vals['customer']
        supplier = vals['supplier']
        if (
            invoice
            and invoice.invoice_date
            and customer.country_id.code in EUROPEAN_ECONOMIC_AREA_COUNTRY_CODES
            and supplier.country_id.code in EUROPEAN_ECONOMIC_AREA_COUNTRY_CODES
            and supplier.country_id != customer.country_id
        ):
            node['cbc:ActualDeliveryDate']['_text'] = invoice.invoice_date
        return node