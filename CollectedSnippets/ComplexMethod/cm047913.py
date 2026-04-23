def _validate_jo_edi_numbers(self, xml_string, amount_total):
        """
        TLDR: This method checks that units sum up to total values.
        ===================================================================================================
        Problem statement:
        When an EDI is submitted to JoFotara portal, multiple validations are executed to ensure invoice data integrity.
        The most important ones of these validations are the following:-
        --------------------------- ▼ invoice line level ▼  ---------------------------
        1. line_extension_amount = (price_unit * quantity) - discount
        2. taxable_amount = line_extension_amount
        3. rounding_amount = line_extension_amount + general_tax_amount + special_tax_amount
        --------------------------- ▼ invoice level ▼ ---------------------------------
        4. tax_exclusive_amount = sum(price_unit * quantity)
        5. tax_inclusive_amount = sum(price_unit * quantity - discount + general_tax_amount + special_tax_amount)
        6. payable_amount = tax_inclusive_amount
        -------------------------------------------------------------------------------
        The JoFotara portal, however, has no tolerance with rounding errors up to 9 decimal places.
        Hence, the reported values are expected to be up to 9 decimal places,
        and the aggregated units should match reported totals up to 9 decimal places.
        Moreover, reported totals have to equal (or at least be as close as possible) to totals stored in Odoo.
        And since the JOD has precision of 3 decimal places, everything is stored in Odoo approximated to 3 decimal places.
        -------------------------------------------------------------------------------
        This method runs validations in a fashion similar to those running on the JoFotara portal.
        It returns all the errors encountered as a string.
        """
        root = self.get_xml_tree_from_string(xml_string)
        error_message = ""

        total_discount = float(root.findtext('./{*}AllowanceCharge/{*}Amount') or 0.0)
        total_tax = float(root.findtext('./{*}TaxTotal/{*}TaxAmount', default=0))

        tax_exclusive_amount = float(root.findtext('./{*}LegalMonetaryTotal/{*}TaxExclusiveAmount'))
        tax_inclusive_amount = float(root.findtext('./{*}LegalMonetaryTotal/{*}TaxInclusiveAmount'))
        self.assertEqual(float_compare(tax_inclusive_amount, amount_total, 2), 0, f'{tax_inclusive_amount} != {amount_total}')
        monetary_values_discount = float(root.findtext('./{*}LegalMonetaryTotal/{*}AllowanceTotalAmount') or 0.0)
        payable_amount = float(root.findtext('./{*}LegalMonetaryTotal/{*}PayableAmount'))

        error_message += self._equality_check({  # They have to be exactly the same, no decimal difference is tolerated
            'Monetary Values discount': monetary_values_discount,
            'Total Discount': total_discount,
        }, up_to_jo_max_dp=False)
        error_message += self._equality_check({  # They have to be exactly the same, no decimal difference is tolerated
            'Payable Amount': payable_amount,
            'Tax Inclusive Amount': tax_inclusive_amount,
        }, up_to_jo_max_dp=False)

        lines = []
        for xml_line in root.findall('./{*}InvoiceLine'):
            line_extension_amount = float(xml_line.findtext('{*}LineExtensionAmount'))
            line = {
                'id': xml_line.findtext('{*}ID'),
                'quantity': float(xml_line.findtext('{*}InvoicedQuantity')),
                'line_extension_amount': line_extension_amount,
                'tax_amount_general': float(xml_line.findtext('{*}TaxTotal/{*}TaxAmount', default=0)),
                'rounding_amount': float(xml_line.findtext('{*}TaxTotal/{*}RoundingAmount', default=line_extension_amount)),  # defaults to line_extension_amount in the absence of taxes
                **self._extract_vals_from_subtotals(
                    subtotals=xml_line.findall('{*}TaxTotal/{*}TaxSubtotal'),
                    defaults={
                        'taxable_amount_general': line_extension_amount,
                        'tax_amount_general_subtotal': 0,
                        'tax_percent': 0,
                        'taxable_amount_special': line_extension_amount,
                        'tax_amount_special': 0,
                        'total_tax_amount': 0,
                    }),
                'price_unit': float(xml_line.findtext('{*}Price/{*}PriceAmount')),
                'discount': float(xml_line.findtext('{*}Price/{*}AllowanceCharge/{*}Amount') or 0.0),
            }
            lines.append(line)
            line_errors = self._equality_check({
                # taxable_amount = line_extension_amount = price_unit * quantity - discount
                'General Taxable Amount': line['taxable_amount_general'],
                'Special Taxable Amount': line['taxable_amount_special'],
                'Line Extension Amount': line['line_extension_amount'],
                'Price Unit * Quantity - Discount': line['price_unit'] * line['quantity'] - line['discount'],
            }) + self._equality_check({
                # rounding_amount = line_extension_amount + total_tax_amount
                'Rounding Amount': line['rounding_amount'],
                'Line Extension Amount + Total Tax': line['line_extension_amount'] + line['total_tax_amount'],
            }) + self._equality_check({
                'General Tax Amount': line['tax_amount_general'],
                'General Tax Amount in subtotal': line['tax_amount_general_subtotal'],
                'Taxable Amount * Tax Percent': (line['taxable_amount_general'] + line['tax_amount_special']) * line['tax_percent'],
            })
            if line_errors:
                error_message += f"Errors on the line {line['id']}\n"
                error_message += line_errors
                error_message += "-------------------------------------------------------------------------\n"

        aggregated_tax_exclusive_amount = self._sum_max_dp(line['price_unit'] * line['quantity'] for line in lines)
        aggregated_tax_inclusive_amount = self._sum_max_dp(line['price_unit'] * line['quantity'] - line['discount'] + line['total_tax_amount'] for line in lines)
        aggregated_tax_amount = sum(line['tax_amount_general'] for line in lines)
        aggregated_discount_amount = sum(line['discount'] for line in lines)

        error_message += self._equality_check({
            'Tax Exclusive Amount': tax_exclusive_amount,
            'Aggregated Tax Exclusive Amount': aggregated_tax_exclusive_amount,
        }) + self._equality_check({
            'Tax Inclusive Amount': tax_inclusive_amount,
            'Aggregated Tax Inclusive Amount': aggregated_tax_inclusive_amount,
            'Tax Exclusive Amount - Total Discount + Total Tax': tax_exclusive_amount - total_discount + sum(line['total_tax_amount'] for line in lines),
        }) + self._equality_check({
            'Tax Amount': total_tax,
            'Aggregated Tax Amount': aggregated_tax_amount,
        }) + self._equality_check({
            'Discount Amount': total_discount,
            'Aggregated Discount Amount': aggregated_discount_amount,
        })

        return error_message