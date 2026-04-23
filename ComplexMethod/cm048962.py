def _get_rounded_base_lines(self):
        """
        The base lines used when exporting the document will highly differ based on whether this is
        or not a consolidated invoice, as well as whether this is for PoS.

        :return: The rounded base lines to be used when exporting the document.
        """
        self.ensure_one()
        # Refunds of consolidated invoices are treated as regular invoice besides for the fixed customer.
        if self._is_consolidated_invoice():
            AccountTax = self.env['account.tax']
            grouped_records = self._split_consolidated_invoice_record_in_lines()

            tax_data_fields = (
                "raw_base_amount_currency",
                "raw_base_amount",
                "raw_tax_amount_currency",
                "raw_tax_amount",
                "base_amount_currency",
                "base_amount",
                "tax_amount_currency",
                "tax_amount",
            )
            consolidated_base_lines = []
            for index, records in enumerate(grouped_records):
                base_lines = []
                for record in records:
                    base_lines += self._get_record_rounded_base_lines(record)

                # Aggregate the base lines into one.
                new_tax_details = {
                    "raw_total_excluded_currency": 0.0,
                    "total_excluded_currency": 0.0,
                    "raw_total_excluded": 0.0,
                    "total_excluded": 0.0,
                    "raw_total_included_currency": 0.0,
                    "total_included_currency": 0.0,
                    "raw_total_included": 0.0,
                    "total_included": 0.0,
                    "delta_total_excluded_currency": 0.0,
                    "delta_total_excluded": 0.0,
                }
                new_taxes_data_map = {}

                taxes = self.env["account.tax"]
                for base_line in base_lines:
                    tax_details = base_line["tax_details"]
                    sign = -1 if base_line["is_refund"] else 1
                    for key in new_tax_details:
                        new_tax_details[key] += sign * tax_details[key]
                    for tax_data in tax_details["taxes_data"]:
                        tax = tax_data["tax"]
                        taxes |= tax
                        if tax in new_taxes_data_map:
                            for key in tax_data_fields:
                                new_taxes_data_map[tax][key] += sign * tax_data[key]
                        else:
                            new_taxes_data_map[tax] = dict(tax_data)
                            for key in tax_data_fields:
                                new_taxes_data_map[tax][key] = sign * tax_data[key]

                total_amount_discounted = new_tax_details["total_excluded"] + new_tax_details["delta_total_excluded"]
                total_amount_discounted_currency = new_tax_details["total_excluded_currency"] + new_tax_details["delta_total_excluded_currency"]
                total_amount = total_amount_currency = 0.0
                for base_line in base_lines:
                    sign = -1 if base_line["is_refund"] else 1
                    total_amount += sign * (
                        (base_line["price_unit"] / base_line["rate"])
                        * base_line["quantity"]
                    )
                    total_amount_currency += sign * (
                        base_line["price_unit"] * base_line["quantity"]
                    )

                # Only compute discount if any base_line has an actual discount percentage
                has_discount = any(base_line['discount'] for base_line in base_lines)
                discount_amount = (total_amount - total_amount_discounted) if has_discount else 0.0
                discount_amount_currency = (total_amount_currency - total_amount_discounted_currency) if has_discount else 0.0

                # for the line name, when consolidating, we want to show first sequence - last sequence
                sequenced_records = records.sorted(key=lambda r: r.name)
                new_base_line = AccountTax._prepare_base_line_for_taxes_computation(
                    {},
                    tax_ids=taxes,
                    price_unit=total_amount_currency,
                    discount_amount=discount_amount,
                    discount_amount_currency=discount_amount_currency,
                    quantity=1.0,
                    currency_id=self.currency_id,
                    tax_details={
                        **new_tax_details,
                        "taxes_data": list(new_taxes_data_map.values()),
                    },
                    line_name=f"{sequenced_records[0].name}-{sequenced_records[-1].name}" if len(sequenced_records) > 1 else sequenced_records[0].name,
                )
                consolidated_base_lines.append(new_base_line)

            base_lines = consolidated_base_lines
        else:
            invoice = self.invoice_ids[0]  # Otherwise it would be a consolidated invoice.
            base_lines, _tax_lines = invoice._get_rounded_base_and_tax_lines()
        # In any cases, we'll provide a reference to the document in the base lines.
        # This will help later on when it is time to handle tax grouping as we may need to get the
        # tax exemption info.
        for base_line in base_lines:
            base_line['myinvois_document'] = self

        return base_lines