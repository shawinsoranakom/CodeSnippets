def _get_rainbowman_message(self):
        self.ensure_one()
        if not self.user_id:
            return False
        self.flush_model()  # flush fields to make sure DB is up to date

        # checked here as it is its position in the priority order
        if len(self.message_ids) >= 25:
            return _('Phew, that took some effort — but you nailed it. Good job!')

        team_condition = f'team_id = {self.team_id.id}' if self.team_id else 'team_id IS NULL'
        source_case = f'source_id = {self.source_id.id} AND {team_condition}' if self.source_id else 'false'
        country_case = f'country_id = {self.country_id.id} AND {team_condition}' if self.country_id else 'false'
        tz_midnight = fields.Datetime.now().astimezone(pytz.timezone(self.env.user.tz or self.user_id.tz or 'UTC')).replace(hour=0, minute=0, second=0)
        tz_midnight_in_utc = tz_midnight.astimezone(pytz.UTC).replace(tzinfo=None)
        query = f"""
        SELECT
            MAX(CASE WHEN team_id = %(team_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '31 days' AND id <> %(lead_id)s THEN expected_revenue ELSE 0 END) AS max_team_31,
            MAX(CASE WHEN team_id = %(team_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '7 days'  AND id <> %(lead_id)s THEN expected_revenue ELSE 0 END) AS max_team_7,
            MAX(CASE WHEN user_id = %(user_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '31 days' AND id <> %(lead_id)s THEN expected_revenue ELSE 0 END) AS max_user_31,
            MAX(CASE WHEN user_id = %(user_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '7 days'  AND id <> %(lead_id)s THEN expected_revenue ELSE 0 END) AS max_user_7,
            MIN(CASE WHEN COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '31 days' THEN day_close ELSE 31 END) AS min_day_close_31,
            COUNT(CASE WHEN user_id = %(user_id)s THEN 1 ELSE NULL END) AS count_user_closed_year,
            COUNT(CASE WHEN user_id = %(user_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '3 days' AND COALESCE(date_closed, create_date) < %(tz_midnight)s - INTERVAL '2 days' THEN 1 ELSE NULL END) AS count_user_closed_minus3day,
            COUNT(CASE WHEN user_id = %(user_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '2 days' AND COALESCE(date_closed, create_date) < %(tz_midnight)s - INTERVAL '1 days' THEN 1 ELSE NULL END) AS count_user_closed_minus2day,
            COUNT(CASE WHEN user_id = %(user_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s - INTERVAL '1 days' AND COALESCE(date_closed, create_date) < %(tz_midnight)s THEN 1 ELSE NULL END) AS count_user_closed_yesterday,
            COUNT(CASE WHEN user_id = %(user_id)s AND COALESCE(date_closed, create_date) >= %(tz_midnight)s THEN 1 ELSE NULL END) AS count_user_closed_today,
            COUNT(CASE WHEN {source_case} THEN 1 ELSE NULL END) AS count_source_closed_year,
            COUNT(CASE WHEN {country_case} THEN 1 ELSE NULL END) AS count_country_closed_year
            FROM crm_lead
            WHERE
                type = 'opportunity'
            AND
                active = True
            AND
                probability = 100
            AND
                DATE_TRUNC('year', COALESCE(date_closed, create_date)) = DATE_TRUNC('year', %(tz_midnight)s)
            AND
                (user_id = %(user_id)s OR team_id = %(team_id)s)
        """
        self.env.cr.execute(query, {
            'user_id': self.env.user.id,
            'team_id': self.team_id.id or -1,
            'lead_id': self.id,
            'tz_midnight': tz_midnight_in_utc,
        })
        query_result = self.env.cr.dictfetchone()

        def _is_lower_than_expected_revenue(value):
            return self.expected_revenue and value is not None and value < self.expected_revenue

        if query_result['count_user_closed_year'] == 1:
            return _('Go, go, go! Congrats for your first deal.')
        elif _is_lower_than_expected_revenue(query_result['max_team_31']):
            return _('Boom! Team record for the past 30 days.')
        elif _is_lower_than_expected_revenue(query_result['max_team_7']):
            return _('Yeah! Best deal out of the last 7 days for the team.')
        elif _is_lower_than_expected_revenue(query_result['max_user_31']):
            return _('You just beat your personal record for the past 30 days.')
        elif _is_lower_than_expected_revenue(query_result['max_user_7']):
            return _('You just beat your personal record for the past 7 days.')
        elif query_result['count_user_closed_today'] == 5:
            return _('You\'re on fire! Fifth deal won today 🔥')
        elif query_result['count_user_closed_today'] == 1 and query_result['count_user_closed_yesterday'] and query_result['count_user_closed_minus2day'] and not query_result['count_user_closed_minus3day']:
            return _('You\'re on a winning streak. 3 deals in 3 days, congrats!')
        # check that at least one minute has elapsed since record creation to only account for 'real' leads
        elif query_result['min_day_close_31'] == self.day_close and self.day_close < 31 \
            and self.date_closed and (self.date_closed - self.create_date).total_seconds() > 60:
            return _('Wow, that was fast. That deal didn’t stand a chance!')
        # use duration tracking field to determine if the task jumped from first to last stage
        # only takes into accounts stages on which the lead has spent at least a minute,
        # to only account for valid stage movements
        elif len(stage_ids := [int(stage_id) for stage_id, duration in self.duration_tracking.items() if duration >= 60]) == 1:
            first_stage = self.env['crm.stage'].search([
                '|', ('team_ids', 'in', False), ('team_ids', 'in', self.team_id.id),
            ], order='sequence ASC', limit=1)
            if first_stage.id == stage_ids[0]:
                return _('No detours, no delays - from %(stage_name)s straight to the win! 🚀', stage_name=first_stage.name)
        if query_result['count_country_closed_year'] == 1 and self.country_id:
            return _('You just expanded the map! First win in %(country)s.', country=self.country_id.name)
        elif query_result['count_source_closed_year'] == 1 and self.source_id:
            return _('Yay, your first win from %(utm_source_name)s!', utm_source_name=self.source_id.name)
        return False