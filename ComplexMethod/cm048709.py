def _prepare_counterpart_amounts_using_st_line_rate(self, currency, balance, amount_currency):
        """ Convert the amounts passed as parameters to the statement line currency using the rates provided by the
        bank. The computed amounts are the one that could be set on the statement line as a counterpart journal item
        to fully paid the provided amounts as parameters.

        :param currency:        The currency in which is expressed 'amount_currency'.
        :param balance:         The amount expressed in company currency. Only needed when the currency passed as
                                parameter is neither the statement line's foreign currency, neither the journal's
                                currency.
        :param amount_currency: The amount expressed in the 'currency' passed as parameter.
        :return:                A python dictionary containing:
            * balance:          The amount to consider expressed in company's currency.
            * amount_currency:  The amount to consider expressed in statement line's foreign currency.
        """
        self.ensure_one()

        transaction_amount, transaction_currency, journal_amount, journal_currency, company_amount, company_currency \
            = self._get_accounting_amounts_and_currencies()

        rate_journal2foreign_curr = journal_amount and abs(transaction_amount) / abs(journal_amount)
        rate_comp2journal_curr = company_amount and abs(journal_amount) / abs(company_amount)

        if currency == transaction_currency:
            trans_amount_currency = amount_currency
            if rate_journal2foreign_curr:
                journ_amount_currency = journal_currency.round(trans_amount_currency / rate_journal2foreign_curr)
            else:
                journ_amount_currency = 0.0
            if rate_comp2journal_curr:
                new_balance = company_currency.round(journ_amount_currency / rate_comp2journal_curr)
            else:
                new_balance = 0.0
        elif currency == journal_currency:
            trans_amount_currency = transaction_currency.round(amount_currency * rate_journal2foreign_curr)
            if rate_comp2journal_curr:
                new_balance = company_currency.round(amount_currency / rate_comp2journal_curr)
            else:
                new_balance = 0.0
        else:
            journ_amount_currency = journal_currency.round(balance * rate_comp2journal_curr)
            trans_amount_currency = transaction_currency.round(journ_amount_currency * rate_journal2foreign_curr)
            new_balance = balance

        return {
            'amount_currency': trans_amount_currency,
            'balance': new_balance,
        }