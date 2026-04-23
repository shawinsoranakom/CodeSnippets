def _import_ubl_invoice_add_customer_values(self, collected_values):
        customer_values = collected_values['customer_values'] = {}
        odoo_document_type = collected_values['odoo_document_type']
        party_tag = "AccountingCustomerParty" if odoo_document_type == 'sale' else "AccountingSupplierParty"
        tree = collected_values['tree']
        party_node = tree.find(f"./{{*}}{party_tag}/{{*}}Party")
        if party_node is None:
            return

        for key, xpaths in (
            ('vat', [".//{*}CompanyID"]),
            ('phone', [".//{*}Telephone"]),
            ('name', [
                ".//{*}RegistrationName",
                ".//{*}Name",
            ]),
            ('email', [".//{*}ElectronicMail"]),
            ('country_code', [".//{*}Country//{*}IdentificationCode"]),
            ('street', [".//{*}StreetName"]),
            ('street2', [".//{*}AdditionalStreetName"]),
            ('city', [".//{*}CityName"]),
            ('zip', [".//{*}PostalZone"]),
        ):
            customer_values[key] = None
            for xpath in xpaths:
                if (node := party_node.find(xpath)) is not None:
                    customer_values[key] = node.text
                    break

        # Peppol EAS/Endpoint.
        if (node := party_node.find(".//{*}EndpointID")) is not None:
            customer_values['peppol_endpoint'] = node.text
            if peppol_eas := node.attrib.get('schemeID'):
                customer_values['peppol_eas'] = peppol_eas