def _get_formating_options(self, strings):
        options = super()._get_formating_options(strings)
        separators = "-/ "
        date_regex = f'[^{separators}]+'
        for string in strings:
            # Searches for a date.
            date_data = re_findall(date_regex, string)
            if len(date_data) < 2:  # Not enough data.
                continue
            value_1, value_2 = date_data[:2]
            if re_findall('[a-zA-Z]', value_1):
                # Assumes the first value is the mounth (written in letters). Don't add any option
                # as mounth as the first date's value is the default behavior for `dateutil.parse`.
                break
            # Try to guess if the first data is the day or the year.
            if int(value_1) > 31:
                options['yearfirst'] = True
                break
            elif int(value_1) > 12 and (re_findall('[a-zA-Z]', value_2) or int(value_2) <= 12):
                options['dayfirst'] = True
                break
            else:  # Too ambiguous, gets the option from the user's lang's date setting.
                user_lang_format = get_lang(self.env).date_format
                if re_findall('^%[mbB]', user_lang_format):  # First parameter is for month.
                    return options
                elif re_findall('^%[djaA]', user_lang_format):  # First parameter is for day.
                    options['dayfirst'] = True
                    break
                elif re_findall('^%[yY]', user_lang_format):  # First parameter is for year.
                    options['yearfirst'] = True
                    break
        return options