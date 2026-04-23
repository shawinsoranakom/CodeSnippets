def __find_month_format(self, directive):
        """Find the month format appropriate for the current locale.

        In some locales (for example French and Hebrew), the default month
        used in __calc_date_time has the same name in full and abbreviated
        form.  Also, the month name can by accident match other part of the
        representation: the day of the week name (for example in Morisyen)
        or the month number (for example in Japanese).  Thus, cycle months
        of the year and find all positions that match the month name for
        each month,  If no common positions are found, the representation
        does not use the month name.
        """
        full_indices = abbr_indices = None
        for m in range(1, 13):
            time_tuple = time.struct_time((1999, m, 17, 22, 44, 55, 2, 76, 0))
            datetime = time.strftime(directive, time_tuple).lower()
            indices = set(_findall(datetime, self.f_month[m]))
            if full_indices is None:
                full_indices = indices
            else:
                full_indices &= indices
            indices = set(_findall(datetime, self.a_month[m]))
            if abbr_indices is None:
                abbr_indices = set(indices)
            else:
                abbr_indices &= indices
            if not full_indices and not abbr_indices:
                return None, None
        if full_indices:
            return self.f_month, '%B'
        if abbr_indices:
            return self.a_month, '%b'
        return None, None