def _test_taxes_l10n_in(self):
        """ Test suite for the complex GST taxes in l10n_in. This case implies 3 percentage taxes:
        t1: % tax, include_base_amount
        t2: same % as t1, include_base_amount, not is_base_affected
        t3: % tax

        This case is complex because the amounts of t1 and t2 must always be the same.
        Furthermore, it's a complicated setup due to the usage of include_base_amount / is_base_affected.
        """
        tax1 = self.percent_tax(6, include_base_amount=True, tax_group_id=self.tax_groups[0].id)
        tax2 = self.percent_tax(6, include_base_amount=True, is_base_affected=False, tax_group_id=self.tax_groups[1].id)
        tax3 = self.percent_tax(3, tax_group_id=self.tax_groups[2].id)
        taxes = tax1 + tax2 + tax3

        document_params = self.init_document(
            lines=[
                {'price_unit': 15.89, 'tax_ids': taxes},
                {'price_unit': 15.89, 'tax_ids': taxes},
            ],
            currency=self.foreign_currency,
            rate=5.0,
        )
        with self.with_tax_calculation_rounding_method('round_per_line'):
            document = self.populate_document(document_params)
            self.assert_py_tax_totals_summary(document, {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.78,
                'base_amount': 6.36,
                'tax_amount_currency': 4.86,
                'tax_amount': 0.98,
                'total_amount_currency': 36.64,
                'total_amount': 7.34,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.78,
                        'base_amount': 6.36,
                        'tax_amount_currency': 4.86,
                        'tax_amount': 0.98,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.78,
                                'base_amount': 6.36,
                                'tax_amount_currency': 1.9,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.78,
                                'display_base_amount': 6.36,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.78,
                                'base_amount': 6.36,
                                'tax_amount_currency': 1.9,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.78,
                                'display_base_amount': 6.36,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 35.58,
                                'base_amount': 7.12,
                                'tax_amount_currency': 1.06,
                                'tax_amount': 0.22,
                                'display_base_amount_currency': 35.58,
                                'display_base_amount': 7.12,
                            },
                        ],
                    },
                ],
            })

            # Discount 2%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.15,
                'base_amount': 6.23,
                'tax_amount_currency': 4.76,
                'tax_amount': 0.96,
                'total_amount_currency': 35.91,
                'total_amount': 7.19,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.15,
                        'base_amount': 6.23,
                        'tax_amount_currency': 4.76,
                        'tax_amount': 0.96,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.14,
                                'base_amount': 6.23,
                                'tax_amount_currency': 1.86,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.14,
                                'display_base_amount': 6.23,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.14,
                                'base_amount': 6.23,
                                'tax_amount_currency': 1.86,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.1414,
                                'display_base_amount': 6.23,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 34.87,
                                'base_amount': 6.98,
                                'tax_amount_currency': 1.04,
                                'tax_amount': 0.22,
                                'display_base_amount_currency': 34.87,
                                'display_base_amount': 6.98,
                            },
                        ],
                    },
                ],
            }
            yield "round_per_line, price_excluded", document, False, 'percent', 2, expected_values

            # Discount 3-6%
            for percent in range(3, 7):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.64 * (100 - percent) / 100.0)}
                yield "round_per_line, price_excluded", document, True, 'percent', percent, expected_values

            # Discount 7%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 29.55,
                'base_amount': 5.93,
                'tax_amount_currency': 4.53,
                'tax_amount': 0.9,
                'total_amount_currency': 34.08,
                'total_amount': 6.83,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 29.55,
                        'base_amount': 5.93,
                        'tax_amount_currency': 4.53,
                        'tax_amount': 0.9,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 29.56,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.77,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.56,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 29.56,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.77,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.56,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 33.09,
                                'base_amount': 6.62,
                                'tax_amount_currency': 0.99,
                                'tax_amount': 0.2,
                                'display_base_amount_currency': 33.09,
                                'display_base_amount': 6.62,
                            },
                        ],
                    },
                ],
            }
            yield "round_per_line, price_excluded", document, False, 'percent', 7, expected_values

            # Discount 8-17%
            for percent in range(8, 18):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.64 * (100 - percent) / 100.0)}
                yield "round_per_line, price_excluded", document, True, 'percent', percent, expected_values

            # Discount 18%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 26.05,
                'base_amount': 5.22,
                'tax_amount_currency': 3.99,
                'tax_amount': 0.8,
                'total_amount_currency': 30.04,
                'total_amount': 6.02,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 26.05,
                        'base_amount': 5.22,
                        'tax_amount_currency': 3.99,
                        'tax_amount': 0.8,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 26.06,
                                'base_amount': 5.22,
                                'tax_amount_currency': 1.56,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.06,
                                'display_base_amount': 5.22,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 26.06,
                                'base_amount': 5.22,
                                'tax_amount_currency': 1.56,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.06,
                                'display_base_amount': 5.22,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 29.18,
                                'base_amount': 5.84,
                                'tax_amount_currency': 0.87,
                                'tax_amount': 0.18,
                                'display_base_amount_currency': 29.18,
                                'display_base_amount': 5.84,
                            },
                        ],
                    },
                ],
            }
            yield "round_per_line, price_excluded", document, False, 'percent', 18, expected_values

            # Discount 19-20%
            for percent in range(19, 21):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.64 * (100 - percent) / 100.0)}
                yield "round_per_line, price_excluded", document, True, 'percent', percent, expected_values

        with self.with_tax_calculation_rounding_method('round_globally'):
            document = self.populate_document(document_params)
            self.assert_py_tax_totals_summary(document, {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.78,
                'base_amount': 6.36,
                'tax_amount_currency': 4.89,
                'tax_amount': 0.97,
                'total_amount_currency': 36.67,
                'total_amount': 7.33,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.78,
                        'base_amount': 6.36,
                        'tax_amount_currency': 4.89,
                        'tax_amount': 0.97,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.78,
                                'base_amount': 6.36,
                                'tax_amount_currency': 1.91,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.78,
                                'display_base_amount': 6.36,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.78,
                                'base_amount': 6.36,
                                'tax_amount_currency': 1.91,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.78,
                                'display_base_amount': 6.36,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 35.59,
                                'base_amount': 7.12,
                                'tax_amount_currency': 1.07,
                                'tax_amount': 0.21,
                                'display_base_amount_currency': 35.59,
                                'display_base_amount': 7.12,
                            },
                        ],
                    },
                ],
            })

            # Discount 2%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.15,
                'base_amount': 6.23,
                'tax_amount_currency': 4.79,
                'tax_amount': 0.95,
                'total_amount_currency': 35.94,
                'total_amount': 7.18,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.15,
                        'base_amount': 6.23,
                        'tax_amount_currency': 4.79,
                        'tax_amount': 0.95,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.14,
                                'base_amount': 6.23,
                                'tax_amount_currency': 1.87,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.14,
                                'display_base_amount': 6.23,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.14,
                                'base_amount': 6.23,
                                'tax_amount_currency': 1.87,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.14,
                                'display_base_amount': 6.23,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 34.88,
                                'base_amount': 6.98,
                                'tax_amount_currency': 1.05,
                                'tax_amount': 0.21,
                                'display_base_amount_currency': 34.88,
                                'display_base_amount': 6.98,
                            },
                        ],
                    },
                ],
            }
            yield "round_globally, price_excluded", document, False, 'percent', 2, expected_values

            # Discount 3-6%
            for percent in range(3, 7):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.67 * (100 - percent) / 100.0)}
                yield "round_globally, price_excluded", document, True, 'percent', percent, expected_values

            # Discount 7%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 29.54,
                'base_amount': 5.92,
                'tax_amount_currency': 4.56,
                'tax_amount': 0.9,
                'total_amount_currency': 34.1,
                'total_amount': 6.82,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 29.54,
                        'base_amount': 5.92,
                        'tax_amount_currency': 4.56,
                        'tax_amount': 0.9,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 29.56,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.78,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.56,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 29.56,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.78,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.56,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 33.1,
                                'base_amount': 6.62,
                                'tax_amount_currency': 1.0,
                                'tax_amount': 0.20,
                                'display_base_amount_currency': 33.1,
                                'display_base_amount': 6.62,
                            },
                        ],
                    },
                ],
            }
            yield "round_globally, price_excluded", document, False, 'percent', 7, expected_values

            # Discount 8-17%
            for percent in range(8, 18):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.67 * (100 - percent) / 100.0)}
                yield "round_globally, price_excluded", document, True, 'percent', percent, expected_values

            # Discount 18%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 26.05,
                'base_amount': 5.22,
                'tax_amount_currency': 4.02,
                'tax_amount': 0.79,
                'total_amount_currency': 30.07,
                'total_amount': 6.01,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 26.05,
                        'base_amount': 5.22,
                        'tax_amount_currency': 4.02,
                        'tax_amount': 0.79,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 26.06,
                                'base_amount': 5.22,
                                'tax_amount_currency': 1.57,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.06,
                                'display_base_amount': 5.22,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 26.06,
                                'base_amount': 5.22,
                                'tax_amount_currency': 1.57,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.06,
                                'display_base_amount': 5.22,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 29.18,
                                'base_amount': 5.84,
                                'tax_amount_currency': 0.88,
                                'tax_amount': 0.17,
                                'display_base_amount_currency': 29.18,
                                'display_base_amount': 5.84,
                            },
                        ],
                    },
                ],
            }
            yield "round_globally, price_excluded", document, False, 'percent', 18, expected_values

            # Discount 19-20%
            for percent in range(19, 21):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.67 * (100 - percent) / 100.0)}
                yield "round_globally, price_excluded", document, True, 'percent', percent, expected_values

        tax1.price_include_override = 'tax_included'
        tax2.price_include_override = 'tax_included'

        document_params = self.init_document(
            lines=[
                {'price_unit': 17.79, 'tax_ids': taxes},
                {'price_unit': 17.79, 'tax_ids': taxes},
            ],
            currency=self.foreign_currency,
            rate=5.0,
        )
        with self.with_tax_calculation_rounding_method('round_per_line'):
            document = self.populate_document(document_params)
            self.assert_py_tax_totals_summary(document, {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.78,
                'base_amount': 6.36,
                'tax_amount_currency': 4.86,
                'tax_amount': 0.98,
                'total_amount_currency': 36.64,
                'total_amount': 7.34,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.78,
                        'base_amount': 6.36,
                        'tax_amount_currency': 4.86,
                        'tax_amount': 0.98,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.78,
                                'base_amount': 6.36,
                                'tax_amount_currency': 1.9,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.78,
                                'display_base_amount': 6.36,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.78,
                                'base_amount': 6.36,
                                'tax_amount_currency': 1.9,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.78,
                                'display_base_amount': 6.36,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 35.58,
                                'base_amount': 7.12,
                                'tax_amount_currency': 1.06,
                                'tax_amount': 0.22,
                                'display_base_amount_currency': 35.58,
                                'display_base_amount': 7.12,
                            },
                        ],
                    },
                ],
            })

            # Discount 2%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.15,
                'base_amount': 6.23,
                'tax_amount_currency': 4.76,
                'tax_amount': 0.96,
                'total_amount_currency': 35.91,
                'total_amount': 7.19,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.15,
                        'base_amount': 6.23,
                        'tax_amount_currency': 4.76,
                        'tax_amount': 0.96,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.14,
                                'base_amount': 6.23,
                                'tax_amount_currency': 1.86,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.14,
                                'display_base_amount': 6.23,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.14,
                                'base_amount': 6.23,
                                'tax_amount_currency': 1.86,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.14,
                                'display_base_amount': 6.23,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 34.87,
                                'base_amount': 6.98,
                                'tax_amount_currency': 1.04,
                                'tax_amount': 0.22,
                                'display_base_amount_currency': 34.87,
                                'display_base_amount': 6.98,
                            },
                        ],
                    },
                ],
            }
            yield "round_per_line, price_included", document, False, 'percent', 2, expected_values

            # Discount 3-6%
            for percent in range(3, 7):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.64 * (100 - percent) / 100.0)}
                yield "round_per_line, price_included", document, True, 'percent', percent, expected_values

            # Discount 7%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 29.55,
                'base_amount': 5.93,
                'tax_amount_currency': 4.53,
                'tax_amount': 0.9,
                'total_amount_currency': 34.08,
                'total_amount': 6.83,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 29.55,
                        'base_amount': 5.93,
                        'tax_amount_currency': 4.53,
                        'tax_amount': 0.9,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 29.56,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.77,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.56,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 29.56,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.77,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.56,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 33.09,
                                'base_amount': 6.62,
                                'tax_amount_currency': 0.99,
                                'tax_amount': 0.2,
                                'display_base_amount_currency': 33.09,
                                'display_base_amount': 6.62,
                            },
                        ],
                    },
                ],
            }
            yield "round_per_line, price_included", document, False, 'percent', 7, expected_values

            # Discount 8-17%
            for percent in range(8, 18):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.64 * (100 - percent) / 100.0)}
                yield "round_per_line, price_included", document, True, 'percent', percent, expected_values

            # Discount 18%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 26.05,
                'base_amount': 5.22,
                'tax_amount_currency': 3.99,
                'tax_amount': 0.8,
                'total_amount_currency': 30.04,
                'total_amount': 6.02,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 26.05,
                        'base_amount': 5.22,
                        'tax_amount_currency': 3.99,
                        'tax_amount': 0.8,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 26.06,
                                'base_amount': 5.22,
                                'tax_amount_currency': 1.56,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.06,
                                'display_base_amount': 5.22,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 26.06,
                                'base_amount': 5.22,
                                'tax_amount_currency': 1.56,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.06,
                                'display_base_amount': 5.22,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 29.18,
                                'base_amount': 5.84,
                                'tax_amount_currency': 0.87,
                                'tax_amount': 0.18,
                                'display_base_amount_currency': 29.18,
                                'display_base_amount': 5.84,
                            },
                        ],
                    },
                ],
            }
            yield "round_per_line, price_included", document, False, 'percent', 18, expected_values

            # Discount 19-20%
            for percent in range(19, 21):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.64 * (100 - percent) / 100.0)}
                yield "round_per_line, price_included", document, True, 'percent', percent, expected_values

        with self.with_tax_calculation_rounding_method('round_globally'):
            document = self.populate_document(document_params)
            self.assert_py_tax_totals_summary(document, {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.77,
                'base_amount': 6.35,
                'tax_amount_currency': 4.89,
                'tax_amount': 0.97,
                'total_amount_currency': 36.66,
                'total_amount': 7.32,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.77,
                        'base_amount': 6.35,
                        'tax_amount_currency': 4.89,
                        'tax_amount': 0.97,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.76,
                                'base_amount': 6.35,
                                'tax_amount_currency': 1.91,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.76,
                                'display_base_amount': 6.35,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.76,
                                'base_amount': 6.35,
                                'tax_amount_currency': 1.91,
                                'tax_amount': 0.38,
                                'display_base_amount_currency': 31.76,
                                'display_base_amount': 6.35,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 35.58,
                                'base_amount': 7.12,
                                'tax_amount_currency': 1.07,
                                'tax_amount': 0.21,
                                'display_base_amount_currency': 35.58,
                                'display_base_amount': 7.12,
                            },
                        ],
                    },
                ],
            })

            # Discount 2%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 31.14,
                'base_amount': 6.22,
                'tax_amount_currency': 4.79,
                'tax_amount': 0.95,
                'total_amount_currency': 35.93,
                'total_amount': 7.17,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 31.14,
                        'base_amount': 6.22,
                        'tax_amount_currency': 4.79,
                        'tax_amount': 0.95,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 31.12,
                                'base_amount': 6.22,
                                'tax_amount_currency': 1.87,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.12,
                                'display_base_amount': 6.22,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 31.12,
                                'base_amount': 6.22,
                                'tax_amount_currency': 1.87,
                                'tax_amount': 0.37,
                                'display_base_amount_currency': 31.12,
                                'display_base_amount': 6.22,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 34.87,
                                'base_amount': 6.98,
                                'tax_amount_currency': 1.05,
                                'tax_amount': 0.21,
                                'display_base_amount_currency': 34.87,
                                'display_base_amount': 6.98,
                            },
                        ],
                    },
                ],
            }
            yield "round_globally, price_included", document, False, 'percent', 2, expected_values

            # Discount 3-6%
            for percent in range(3, 7):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.66 * (100 - percent) / 100.0)}
                yield "round_globally, price_included", document, True, 'percent', percent, expected_values

            # Discount 7%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 29.53,
                'base_amount': 5.91,
                'tax_amount_currency': 4.56,
                'tax_amount': 0.9,
                'total_amount_currency': 34.09,
                'total_amount': 6.81,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 29.53,
                        'base_amount': 5.91,
                        'tax_amount_currency': 4.56,
                        'tax_amount': 0.9,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 29.54,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.78,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.54,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 29.54,
                                'base_amount': 5.91,
                                'tax_amount_currency': 1.78,
                                'tax_amount': 0.35,
                                'display_base_amount_currency': 29.54,
                                'display_base_amount': 5.91,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 33.09,
                                'base_amount': 6.62,
                                'tax_amount_currency': 1.0,
                                'tax_amount': 0.20,
                                'display_base_amount_currency': 33.09,
                                'display_base_amount': 6.62,
                            },
                        ],
                    },
                ],
            }
            yield "round_globally, price_included", document, False, 'percent', 7, expected_values

            # Discount 8-17%
            for percent in range(8, 18):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.66 * (100 - percent) / 100.0)}
                yield "round_globally, price_included", document, True, 'percent', percent, expected_values

            # Discount 18%
            expected_values = {
                'same_tax_base': False,
                'currency_id': self.foreign_currency.id,
                'company_currency_id': self.currency.id,
                'base_amount_currency': 26.04,
                'base_amount': 5.21,
                'tax_amount_currency': 4.02,
                'tax_amount': 0.79,
                'total_amount_currency': 30.06,
                'total_amount': 6.0,
                'subtotals': [
                    {
                        'name': "Untaxed Amount",
                        'base_amount_currency': 26.04,
                        'base_amount': 5.21,
                        'tax_amount_currency': 4.02,
                        'tax_amount': 0.79,
                        'tax_groups': [
                            {
                                'id': self.tax_groups[0].id,
                                'base_amount_currency': 26.04,
                                'base_amount': 5.21,
                                'tax_amount_currency': 1.57,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.04,
                                'display_base_amount': 5.21,
                            },
                            {
                                'id': self.tax_groups[1].id,
                                'base_amount_currency': 26.04,
                                'base_amount': 5.21,
                                'tax_amount_currency': 1.57,
                                'tax_amount': 0.31,
                                'display_base_amount_currency': 26.04,
                                'display_base_amount': 5.21,
                            },
                            {
                                'id': self.tax_groups[2].id,
                                'base_amount_currency': 29.18,
                                'base_amount': 5.84,
                                'tax_amount_currency': 0.88,
                                'tax_amount': 0.17,
                                'display_base_amount_currency': 29.18,
                                'display_base_amount': 5.84,
                            },
                        ],
                    },
                ],
            }
            yield "round_globally, price_included", document, False, 'percent', 18, expected_values

            # Discount 19-20%
            for percent in range(19, 21):
                expected_values = {'total_amount_currency': self.foreign_currency.round(36.66 * (100 - percent) / 100.0)}
                yield "round_globally, price_included", document, True, 'percent', percent, expected_values