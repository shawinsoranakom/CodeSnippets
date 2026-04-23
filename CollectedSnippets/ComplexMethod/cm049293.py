def _web_read_group_fill_temporal(self, groups, groupby, aggregates, fill_from=False, fill_to=False, min_groups=False):
        """Helper method for filling date/datetime 'holes' in a result for the first groupby.

        We are in a use case where data are grouped by a date field (typically
        months but it could be any other interval) and displayed in a chart.

        Assume we group records by month, and we only have data for June,
        September and December. By default, plotting the result gives something
        like::

                                                ___
                                      ___      |   |
                                     |   | ___ |   |
                                     |___||___||___|
                                      Jun  Sep  Dec

        The problem is that December data immediately follow September data,
        which is misleading for the user. Adding explicit zeroes for missing
        data gives something like::

                                                           ___
                             ___                          |   |
                            |   |           ___           |   |
                            |___| ___  ___ |___| ___  ___ |___|
                             Jun  Jul  Aug  Sep  Oct  Nov  Dec

        To customize this output, the context key "fill_temporal" can be used
        under its dictionary format, which has 3 attributes : fill_from,
        fill_to, min_groups (see params of this function)

        Fill between bounds:
        Using either `fill_from` and/or `fill_to` attributes, we can further
        specify that at least a certain date range should be returned as
        contiguous groups. Any group outside those bounds will not be removed,
        but the filling will only occur between the specified bounds. When not
        specified, existing groups will be used as bounds, if applicable.
        By specifying such bounds, we can get empty groups before/after any
        group with data.

        If we want to fill groups only between August (fill_from)
        and October (fill_to)::

                                                     ___
                                 ___                |   |
                                |   |      ___      |   |
                                |___| ___ |___| ___ |___|
                                 Jun  Aug  Sep  Oct  Dec

        We still get June and December. To filter them out, we should match
        `fill_from` and `fill_to` with the domain e.g. ``['&',
        ('date_field', '>=', 'YYYY-08-01'), ('date_field', '<', 'YYYY-11-01')]``::

                                         ___
                                    ___ |___| ___
                                    Aug  Sep  Oct

        Minimal filling amount:
        Using `min_groups`, we can specify that we want at least that amount of
        contiguous groups. This amount is guaranteed to be provided from
        `fill_from` if specified, or from the lowest existing group otherwise.
        This amount is not restricted by `fill_to`. If there is an existing
        group before `fill_from`, `fill_from` is still used as the starting
        group for min_groups, because the filling does not apply on that
        existing group. If neither `fill_from` nor `fill_to` is specified, and
        there is no existing group, no group will be returned.

        If we set min_groups = 4::

                                         ___
                                    ___ |___| ___ ___
                                    Aug  Sep  Oct Nov

        :param list groups: groups returned by _read_group
        :param list groupby: list of fields being grouped on
        :param list aggregates: list of "<key_name>:<aggregate specification>"
        :param str fill_from: (inclusive) string representation of a
            date/datetime, start bound of the fill_temporal range
            formats: date -> %Y-%m-%d, datetime -> %Y-%m-%d %H:%M:%S
        :param str fill_to: (inclusive) string representation of a
            date/datetime, end bound of the fill_temporal range
            formats: date -> %Y-%m-%d, datetime -> %Y-%m-%d %H:%M:%S
        :param int min_groups: minimal amount of required groups for the
            fill_temporal range (should be >= 1)
        :rtype: list
        :return: list
        """
        groupby_name = groupby[0]
        field_name = groupby_name.split(':')[0].split(".")[0]
        field = self._fields[field_name]
        if field.type not in ('date', 'datetime') and not (field.type == 'properties' and ':' in groupby_name):
            return groups

        granularity = groupby_name.split(':')[1]
        days_offset = 0
        if granularity == 'week':
            # _read_group week groups are dependent on the
            # locale, so filled groups should be too to avoid overlaps.
            first_week_day = int(get_lang(self.env).week_start) - 1
            days_offset = first_week_day and 7 - first_week_day
        tz = False
        if field.type == 'datetime' and self.env.context.get('tz') in pytz.all_timezones_set:
            tz = pytz.timezone(self.env.context['tz'])

        # existing non null date(time)
        existing = sorted(group_value for group in groups if (group_value := group[0])) or [None]
        # assumption: existing data is sorted by field 'groupby_name'
        existing_from, existing_to = existing[0], existing[-1]
        if fill_from:
            fill_from = Date.to_date(fill_from)
            fill_from = date_utils.start_of(fill_from, granularity) - datetime.timedelta(days=days_offset)
            if tz:
                fill_from = tz.localize(fill_from)
        elif existing_from:
            fill_from = existing_from
        if fill_to:
            fill_to = Date.to_date(fill_to)
            fill_to = date_utils.start_of(fill_to, granularity) - datetime.timedelta(days=days_offset)
            if tz:
                fill_to = tz.localize(fill_to)
        elif existing_to:
            fill_to = existing_to

        if not fill_to and fill_from:
            fill_to = fill_from
        elif not fill_from and fill_to:
            fill_from = fill_to
        if not fill_from and not fill_to:
            return groups

        interval = READ_GROUP_TIME_GRANULARITY[granularity]
        if min_groups > 0:
            fill_to = max(fill_to, fill_from + (min_groups - 1) * interval)

        if fill_from > fill_to:
            return groups

        empty_item = tuple(self._read_group_empty_value(spec) for spec in groupby[1:] + aggregates)
        required_dates = list(date_utils.date_range(fill_from, fill_to, interval))

        if existing[0] is None:
            existing = list(required_dates)
        else:
            existing = sorted(set().union(existing, required_dates))

        groups_mapped = defaultdict(list)
        for group in groups:
            groups_mapped[group[0]].append(group)

        result = []
        for dt in existing:
            if dt in groups_mapped:
                result.extend(groups_mapped[dt])
            else:
                result.append((dt, *empty_item))

        if False in groups_mapped:
            result.extend(groups_mapped[False])

        return result