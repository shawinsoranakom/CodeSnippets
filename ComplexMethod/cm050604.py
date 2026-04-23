def _get_validity_warnings(self, company, partner, currency, date, invoiced_amount=0, only_blocking=False, sales_order=False):
        """
        Check whether all declarations of intent in self are valid for the specified `company`, `partner`, `date` and `currency'.
        The checks for `date` and state of the declaration (except draft) are not considered blocking in case `invoiced_amount` is not positive.
        All other checks are considered blocking (prevent posting).
        Includes all checks from `_get_validity_errors`.
        The checks are different for invoices and sales orders (toggled via kwarg `sales_order`).
        I.e. we do not care about the date for sales orders.
        Return all errors as a list of strings.
        """
        errors = []
        for declaration in self:
            errors.extend(declaration._get_validity_errors(company, partner, currency))
            if declaration.state == 'draft':
                errors.append(_("The Declaration of Intent is in draft."))
            if declaration.currency_id.compare_amounts(invoiced_amount, 0) > 0 or not only_blocking:
                if declaration.state != 'active':
                    errors.append(_("The Declaration of Intent must be active."))
                if not sales_order and (not date or declaration.start_date > date or declaration.end_date < date):
                    errors.append(_("The Declaration of Intent is valid from %(start_date)s to %(end_date)s, not on %(date)s.",
                                    start_date=declaration.start_date, end_date=declaration.end_date, date=date))
        return errors