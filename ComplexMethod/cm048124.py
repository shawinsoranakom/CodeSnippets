def _phone_format(self, fname=False, number=False, country=False, force_format='E164', raise_exception=False):
        """ Format and return number. This number can be found using a field
        (in which case self should be a singleton recordet), or directly given
        if the formatting itself is what matter. Field name can be found
        automatically using :meth:`_phone_get_number_fields`.

        :param str fname: if number is not given, fname indicates the field to
          use to find the number; otherwise use :meth:`_phone_get_number_fields`.;
        :param str number: number to format (in which case fields-based computation
          is skipped);
        :param <res.country> country: country used for formatting number; otherwise
          it is fetched based on record, using :meth:`_phone_get_number_fields`.;
        :param str force_format: stringified version of format globals; should be
          one of ``'E164'``, ``'INTERNATIONAL'``, ``'NATIONAL'`` or ``'RFC3966'``;
        :param bool raise_exception: raise if formatting is not possible (notably
          wrong formatting, invalid country information, ...). Otherwise ``False``
          is returned;

        :return: formatted number. If formatting is not possible ``False`` is
          returned.
        :rtype: str | Literal[False]
        """
        if not number:
            # if no number is given, having a singletong recordset is mandatory to
            # always have a number as input
            self.ensure_one()
            fnames = self._phone_get_number_fields() if not fname else [fname]
            number = next((self[fname] for fname in fnames if fname in self and self[fname]), False)
        if not number:
            return False

        # fetch country info only if self is a singleton recordset allowing to
        # effectively try to find a country
        if not country and self:
            self.ensure_one()
            country = self._phone_get_country().get(self.id)
        if not country:
            country = self.env.company.country_id

        return self._phone_format_number(
            number,
            country=country, force_format=force_format,
            raise_exception=raise_exception,
        )