def _onchange_name_warning(self):
        if self.name and self.name != '/' and self.name <= (self.highest_name or '') and not self.quick_edit_mode:
            self.show_name_warning = True
        else:
            self.show_name_warning = False

        origin_name = self._origin.name
        if not origin_name or origin_name == '/':
            origin_name = self.highest_name
        if (
            self.name and self.name != '/'
            and origin_name and origin_name != '/'
            and self.date == self._origin.date
            and self.journal_id == self._origin.journal_id
        ):
            new_format, new_format_values = self._get_sequence_format_param(self.name)
            origin_format, origin_format_values = self._get_sequence_format_param(origin_name)

            if (
                new_format != origin_format
                or dict(new_format_values, year=0, month=0, seq=0) != dict(origin_format_values, year=0, month=0, seq=0)
            ):
                changed = _(
                    "It was previously '%(previous)s' and it is now '%(current)s'.",
                    previous=origin_name,
                    current=self.name,
                )
                reset = self._deduce_sequence_number_reset(self.name)
                if reset == 'month':
                    detected = _(
                        "The sequence will restart at 1 at the start of every month.\n"
                        "The year detected here is '%(year)s' and the month is '%(month)s'.\n"
                        "The incrementing number in this case is '%(formatted_seq)s'."
                    )
                elif reset == 'year':
                    detected = _(
                        "The sequence will restart at 1 at the start of every year.\n"
                        "The year detected here is '%(year)s'.\n"
                        "The incrementing number in this case is '%(formatted_seq)s'."
                    )
                elif reset == 'year_range':
                    detected = _(
                        "The sequence will restart at 1 at the start of every financial year.\n"
                        "The financial start year detected here is '%(year)s'.\n"
                        "The financial end year detected here is '%(year_end)s'.\n"
                        "The incrementing number in this case is '%(formatted_seq)s'."
                    )
                elif reset == 'year_range_month':
                    detected = _(
                        "The sequence will restart at 1 at the start of every month.\n"
                        "The financial start year detected here is '%(year)s'.\n"
                        "The financial end year detected here is '%(year_end)s'.\n"
                        "The month detected here is '%(month)s'.\n"
                        "The incrementing number in this case is '%(formatted_seq)s'."
                    )
                else:
                    detected = _(
                        "The sequence will never restart.\n"
                        "The incrementing number in this case is '%(formatted_seq)s'."
                    )
                new_format_values['formatted_seq'] = "{seq:0{seq_length}d}".format(**new_format_values)
                detected = detected % new_format_values
                return {'warning': {
                    'title': _("The sequence format has changed."),
                    'message': "%s\n\n%s" % (changed, detected)
                }}