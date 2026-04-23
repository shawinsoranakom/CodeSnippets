def _l10n_in_edi_generate_invoice_json_managing_negative_lines(self, json_payload):
        """Set negative lines against positive lines as discount with same HSN code and tax rate
            With negative lines
            product name | hsn code | unit price | qty | discount | total
            =============================================================
            product A    | 123456   | 1000       | 1   | 100      |  900
            product B    | 123456   | 1500       | 2   | 0        | 3000
            Discount     | 123456   | -300       | 1   | 0        | -300
            Converted to without negative lines
            product name | hsn code | unit price | qty | discount | total
            =============================================================
            product A    | 123456   | 1000       | 1   | 100      |  900
            product B    | 123456   | 1500       | 2   | 300      | 2700
            totally discounted lines are kept as 0, though
        """
        def discount_group_key(line_vals):
            return "%s-%s" % (line_vals['HsnCd'], line_vals['GstRt'])

        def put_discount_on(discount_line_vals, other_line_vals):
            discount = -discount_line_vals['AssAmt']
            discount_to_allow = other_line_vals['AssAmt']
            in_round = self._l10n_in_round_value
            amount_keys = (
                'AssAmt', 'IgstAmt', 'CgstAmt', 'SgstAmt', 'CesAmt',
                'CesNonAdvlAmt', 'StateCesAmt', 'StateCesNonAdvlAmt',
                'OthChrg', 'TotItemVal'
            )
            if float_compare(discount_to_allow, discount, precision_rounding=self.currency_id.rounding) < 0:
                # Update discount line, needed when discount is more then max line, in short remaining_discount is not zero
                discount_line_vals.update({
                    key: in_round(discount_line_vals[key] + other_line_vals[key])
                    for key in amount_keys
                })
                other_line_vals['Discount'] = in_round(other_line_vals['Discount'] + discount_to_allow)
                other_line_vals.update(dict.fromkeys(amount_keys, 0.00))
                return False
            other_line_vals['Discount'] = in_round(other_line_vals['Discount'] + discount)
            other_line_vals.update({
                key: in_round(other_line_vals[key] + discount_line_vals[key])
                for key in amount_keys
            })
            return True

        discount_lines = []
        for discount_line in json_payload['ItemList'].copy(): #to be sure to not skip in the loop:
            if discount_line['AssAmt'] < 0:
                discount_lines.append(discount_line)
                json_payload['ItemList'].remove(discount_line)
        if not discount_lines:
            return json_payload
        self.message_post(
            author_id=self.env.ref('base.partner_root').id,
            body=_("Negative lines will be decreased from positive invoice lines having the same taxes and HSN code")
        )

        lines_grouped_and_sorted = defaultdict(list)
        for line in sorted(json_payload['ItemList'], key=lambda i: i['AssAmt'], reverse=True):
            lines_grouped_and_sorted[discount_group_key(line)].append(line)

        for discount_line in discount_lines:
            for apply_discount_on in lines_grouped_and_sorted[discount_group_key(discount_line)]:
                if put_discount_on(discount_line, apply_discount_on):
                    break
        return json_payload