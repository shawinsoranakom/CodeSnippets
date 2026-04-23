def _search_new_account_code(self, start_code, cache=None):
        """ Get an account code that is available for creating a new account in the active
            company by starting from an existing code and incrementing it.

            Examples:

            +--------------+-----------------------------------------------------------+
            |  start_code  | codes checked for availability                            |
            +==============+===========================================================+
            |    102100    | 102101, 102102, 102103, 102104, ...                       |
            +--------------+-----------------------------------------------------------+
            |     1598     | 1599, 1600, 1601, 1602, ...                               |
            +--------------+-----------------------------------------------------------+
            |   10.01.08   | 10.01.09, 10.01.10, 10.01.11, 10.01.12, ...               |
            +--------------+-----------------------------------------------------------+
            |   10.01.97   | 10.01.98, 10.01.99, 10.01.97.copy2, 10.01.97.copy3, ...   |
            +--------------+-----------------------------------------------------------+
            |    1021A     | 1021A, 1022A, 1023A, 1024A, ...                           |
            +--------------+-----------------------------------------------------------+
            |    hello     | hello.copy, hello.copy2, hello.copy3, hello.copy4, ...    |
            +--------------+-----------------------------------------------------------+
            |     9998     | 9999, 9998.copy, 9998.copy2, 9998.copy3, ...              |
            +--------------+-----------------------------------------------------------+

            :param str start_code: the code to increment until an available one is found
            :param set[str] cache: a set of codes which you know are already used
                                    (optional, to speed up the method).
                                    If none is given, the method will use cache = ``{start_code}``.
                                    i.e. the method will return the first available code
                                    *strictly* greater than start_code.
                                    If you want the method to start at start_code, you should
                                    explicitly pass cache={}.

            :return: an available new account code for the active company.
                     It will normally have length ``len(start_code)``.
                     If incrementing the last digits starting from ``start_code`` does
                     not work, the method will try as a fallback
                     ``'{start_code}.copy'``, ``'{start_code}.copy2'``, ...
                     ``'{start_code}.copy99'``.
            :rtype: str
        """
        if cache is None:
            cache = {start_code}

        def code_is_available(new_code):
            """ Determine whether `new_code` is available in the active company.

                A code is available for creating a new account in a company if no account
                with the same code belongs to a parent or a child company.

                We use the same definition of availability in `_ensure_code_is_unique`
                and both methods need to be kept in sync.
            """
            return (
                new_code not in cache
                and not self.with_context(active_test=False).sudo().search_count([
                    ('code', '=', new_code),
                    '|',
                    ('company_ids', 'parent_of', self.env.company.id),
                    ('company_ids', 'child_of', self.env.company.id),
                ], limit=1)
            )

        if code_is_available(start_code):
            return start_code

        start_str, digits_str, end_str = ACCOUNT_CODE_NUMBER_REGEX.match(start_code).groups()

        if digits_str != '':
            d, n = len(digits_str), int(digits_str)
            for num in range(n+1, 10**d):
                if code_is_available(new_code := f'{start_str}{num:0{d}}{end_str}'):
                    return new_code

        for num in range(99):
            if code_is_available(new_code := f'{start_code}.copy{num and num + 1 or ""}'):
                return new_code

        raise UserError(_('Cannot generate an unused account code.'))