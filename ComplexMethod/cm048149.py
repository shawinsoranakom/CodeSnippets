def _rrule_parse(self, rule_str, date_start):
        # LUL TODO clean this mess
        data = {}
        day_list = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

        # Skip X-named RRULE extensions
        # TODO Remove patch when dateutils contains the fix
        # HACK https://github.com/dateutil/dateutil/pull/1374
        # Optional parameters starts with X- and they can be placed anywhere in the RRULE string.
        # RRULE:FREQ=MONTHLY;INTERVAL=3;X-RELATIVE=1
        # RRULE;X-EVOLUTION-ENDDATE=20200120:FREQ=WEEKLY;COUNT=3;BYDAY=MO
        # X-EVOLUTION-ENDDATE=20200120:FREQ=WEEKLY;COUNT=3;BYDAY=MO
        rule_str = re.sub(r';?X-[-\w]+=[^;:]*', '', rule_str).replace(":;", ":").lstrip(":;")

        if 'Z' in rule_str and date_start and not date_start.tzinfo:
            date_start = pytz.utc.localize(date_start)
        rule = rrule.rrulestr(rule_str, dtstart=date_start)

        data['rrule_type'] = freq_to_select(rule._freq)
        data['count'] = rule._count
        data['interval'] = rule._interval
        data['until'] = rule._until
        # Repeat weekly
        if rule._byweekday:
            for weekday in day_list:
                data[weekday] = False  # reset
            for weekday_index in rule._byweekday:
                weekday = rrule.weekday(weekday_index)
                data[weekday_to_field(weekday.weekday)] = True
                data['rrule_type'] = 'weekly'

        # Repeat monthly by nweekday ((weekday, weeknumber), )
        if rule._bynweekday:
            data['weekday'] = day_list[list(rule._bynweekday)[0][0]].upper()
            data['byday'] = str(list(rule._bynweekday)[0][1])
            data['month_by'] = 'day'
            data['rrule_type'] = 'monthly'

        if rule._bymonthday and data['rrule_type'] == 'monthly':
            data['day'] = list(rule._bymonthday)[0]
            data['month_by'] = 'date'

        if data.get('until'):
            data['end_type'] = 'end_date'
        elif data.get('count'):
            data['end_type'] = 'count'
        else:
            data['end_type'] = 'forever'
        return data