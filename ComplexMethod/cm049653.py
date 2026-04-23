def _invoice_constraints_eracun_new(self, invoice, vals):
        # Corresponds to Croatian eRacun format constrains
        constraints = {}
        if vals['document_type'] in ['invoice', 'credit_note']:
            for node in vals['document_node']['cac:PaymentMeans']:
                payee_account = node.get('cac:PayeeFinancialAccount')
                if payee_account and any(char.isspace() for char in payee_account['cbc:ID']['_text']):
                    constraints['ubl_hr_br_1'] = self.env._("HR-BR-1: The account number must not contain whitespace characters.")
            if invoice.amount_residual > 0 and not invoice.invoice_date_due:
                constraints.update({'ubl_hr_br_4': self.env._("HR-BT-4: In the case of a positive amount due for payment (BT-115), the payment due date (BT-9) must be specified.")})
            constraints.update({
                'ubl_hr_br_7_seller_email_required': (
                    self.env._("The Seller's e-mail must be provided.")
                ) if not vals['document_node']['cac:AccountingSupplierParty']['cac:Party']['cac:Contact']['cbc:ElectronicMail'].get('_text') else None,
                'ubl_hr_br_10_buyer_email_required': (
                    self.env._("The Buyer's e-mail must be provided.")
                ) if not vals['document_node']['cac:AccountingCustomerParty']['cac:Party']['cac:Contact']['cbc:ElectronicMail'].get('_text') else None,
                'ubl_hr_br_s_buyer_vat_required': (
                    self.env._("The invoice must contain the Customer's VAT identification number (BT-48).")
                ) if any(not item['cbc:CompanyID'].get('_text') for item in vals['document_node']['cac:AccountingCustomerParty']['cac:Party']['cac:PartyTaxScheme']) else None,
                'ubl_hr_br_37_operator_label_required': (
                    self.env._("The invoice must contain the Operator Label (HR-BT-4).")
                ) if not vals['document_node']['cac:AccountingSupplierParty']['cac:SellerContact']['cbc:Name'].get('_text') else None,
                'ubl_hr_br_9_operator_oib_required': (
                    self.env._("The invoice must contain the Operator OIB (HR-BT-5).")
                ) if not vals['document_node']['cac:AccountingSupplierParty']['cac:SellerContact']['cbc:ID'].get('_text') else None,
            })
        return constraints