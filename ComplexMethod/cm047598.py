def filtered(self, func: str | Callable[[Self], bool] | Domain) -> Self:
        """Return the records in ``self`` satisfying ``func``.

        :param func: a function, Domain or a dot-separated sequence of field names
        :return: recordset of records satisfying func, may be empty.

        .. code-block:: python3

            # only keep records whose company is the current user's
            records.filtered(lambda r: r.company_id == user.company_id)

            # only keep records whose partner is a company
            records.filtered("partner_id.is_company")
        """
        if not func:
            # align with mapped()
            return self
        if callable(func):
            # normal function
            pass
        elif isinstance(func, str):
            if '.' in func:
                return self.browse(rec_id for rec_id, rec in zip(self._ids, self) if any(rec.mapped(func)))
            # avoid costly mapped
            func = self._fields[func].__get__
        elif isinstance(func, Domain):
            return self.filtered_domain(func)
        else:
            raise TypeError(f"Invalid function {func!r} to filter on {self._name}")
        return self.browse(rec_id for rec_id, rec in zip(self._ids, self) if func(rec))