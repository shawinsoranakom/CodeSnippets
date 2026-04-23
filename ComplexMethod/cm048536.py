def _prepare_my_invoices_values(self, page, date_begin, date_end, sortby, filterby, domain=None, url="/my/invoices"):
        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env['account.move']

        domain = Domain(domain or Domain.TRUE) & self._get_invoices_domain()

        searchbar_sortings = self._get_account_searchbar_sortings()
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = self._get_account_searchbar_filters()
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        values.update({
            'date': date_begin,
            # content according to pager and archive selected
            # lambda function to get the invoices recordset when the pager will be defined in the main method of a route
            'invoices': lambda pager_offset: (
                [
                    invoice._get_invoice_portal_extra_values()
                    for invoice in AccountInvoice.search(
                        domain, order=order, limit=self._items_per_page, offset=pager_offset
                    )
                ]
                if AccountInvoice.has_access('read') else
                AccountInvoice
            ),
            'page_name': 'invoice',
            'pager': {  # vals to define the pager.
                "url": url,
                "url_args": {'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
                "total": AccountInvoice.search_count(domain) if AccountInvoice.has_access('read') else 0,
                "page": page,
                "step": self._items_per_page,
            },
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'overdue_invoice_count': self._get_overdue_invoice_count(),
        })
        return values