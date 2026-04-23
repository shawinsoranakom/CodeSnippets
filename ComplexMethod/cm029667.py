def __find_weekday_format(self, directive):
        """Find the day of the week format appropriate for the current locale.

        Similar to __find_month_format().
        """
        full_indices = abbr_indices = None
        for wd in range(7):
            time_tuple = time.struct_time((1999, 3, 17, 22, 44, 55, wd, 76, 0))
            datetime = time.strftime(directive, time_tuple).lower()
            indices = set(_findall(datetime, self.f_weekday[wd]))
            if full_indices is None:
                full_indices = indices
            else:
                full_indices &= indices
            if self.f_weekday[wd] != self.a_weekday[wd]:
                indices = set(_findall(datetime, self.a_weekday[wd]))
            if abbr_indices is None:
                abbr_indices = set(indices)
            else:
                abbr_indices &= indices
            if not full_indices and not abbr_indices:
                return None, None
        if full_indices:
            return self.f_weekday, '%A'
        if abbr_indices:
            return self.a_weekday, '%a'
        return None, None