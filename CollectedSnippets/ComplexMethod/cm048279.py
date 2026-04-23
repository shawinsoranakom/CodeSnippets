def _get_operator(
        self, previous_operator_id=None, lang=None, country_id=None, expertises=None, users=None
    ):
        """ Return an operator for a livechat. Try to return the previous
        operator if available. If not, one of the most available operators be
        returned.

        A livechat is considered 'active' if it has at least one message within
        the 30 minutes. This method will try to match the given lang, expertises
        and country_id.

        (Some annoying conversions have to be made on the fly because this model
        holds 'res.users' as available operators and the discuss_channel model
        stores the partner_id of the randomly selected operator)

        :param previous_operator_id: partner id of the previous operator with
            whom the visitor was chatting.
        :param lang: code of the preferred lang of the visitor.
        :param country_id: id of the country of the visitor.
        :param expertises: preferred expertises for filtering operators.
        :param users: recordset of available users to use as candidates instead
            of the users of the livechat channel.
        :return : user
        :rtype : res.users
        """
        self.ensure_one()
        # FIXME: remove inactive call sessions so operators no longer in call are available
        # sudo: required to use garbage collecting function.
        self.env["discuss.channel.rtc.session"].sudo()._gc_inactive_sessions()
        users = users if users is not None else self.available_operator_ids
        if not users:
            return self.env["res.users"]
        if expertises is None:
            expertises = self.env["im_livechat.expertise"]
        self.env.cr.execute(
            """
                WITH operator_rtc_session AS (
                    SELECT COUNT(DISTINCT s.id) as nbr, member.partner_id as partner_id
                      FROM discuss_channel_rtc_session s
                      JOIN discuss_channel_member member ON (member.id = s.channel_member_id)
                  GROUP BY member.partner_id
                )
               SELECT COUNT(DISTINCT h.channel_id), COALESCE(rtc.nbr, 0) > 0 as in_call, h.partner_id
                 FROM im_livechat_channel_member_history h
                 JOIN discuss_channel c ON h.channel_id = c.id
      LEFT OUTER JOIN operator_rtc_session rtc ON rtc.partner_id = h.partner_id
                WHERE c.livechat_end_dt IS NULL
                  AND c.last_interest_dt > ((now() at time zone 'UTC') - interval '30 minutes')
                  AND h.partner_id in %s
             GROUP BY h.partner_id, rtc.nbr
             ORDER BY COUNT(DISTINCT h.channel_id) < 2 OR rtc.nbr IS NULL DESC,
                      COUNT(DISTINCT h.channel_id) ASC,
                      rtc.nbr IS NULL DESC
            """,
            (tuple(users.partner_id.ids),),
        )
        operator_statuses = self.env.cr.dictfetchall()
        # Try to match the previous operator
        if previous_operator_id in users.partner_id.ids:
            previous_operator_status = next(
                (
                    status
                    for status in operator_statuses
                    if status['partner_id'] == previous_operator_id
                ),
                None,
            )
            if not previous_operator_status or previous_operator_status['count'] < 2 or not previous_operator_status['in_call']:
                previous_operator_user = next(
                    available_user
                    for available_user in users
                    if available_user.partner_id.id == previous_operator_id
                )
                return previous_operator_user

        agents_failing_buffer = {
                group[0]
                for group in self.env["im_livechat.channel.member.history"]._read_group(
                    [
                        ("livechat_member_type", "=", "agent"),
                        ("partner_id", "in", users.partner_id.ids),
                        ("channel_id.livechat_end_dt", "=", False),
                        (
                            "create_date",
                            ">",
                            fields.Datetime.now() - timedelta(seconds=BUFFER_TIME),
                        ),
                    ],
                    groupby=["partner_id"],
                )
            }

        def same_language(operator):
            return operator.partner_id.lang == lang or lang in operator.livechat_lang_ids.mapped("code")

        def all_expertises(operator):
            return operator.livechat_expertise_ids >= expertises

        def one_expertise(operator):
            return operator.livechat_expertise_ids & expertises

        def same_country(operator):
            return operator.partner_id.country_id.id == country_id

        # List from most important to least important. Order on each line is irrelevant, all
        # elements of a line must be satisfied together or the next line is checked.
        preferences_list = [
            [same_language, all_expertises],
            [same_language, one_expertise],
            [same_language],
            [same_country, all_expertises],
            [same_country, one_expertise],
            [same_country],
            [all_expertises],
            [one_expertise],
        ]
        for preferences in preferences_list:
            operators = users
            for preference in preferences:
                operators = operators.filtered(preference)
            if operators:
                if agents_respecting_buffer := operators.filtered(
                    lambda op: op.partner_id not in agents_failing_buffer
                ):
                    operators = agents_respecting_buffer
                return self._get_less_active_operator(operator_statuses, operators)
        return self._get_less_active_operator(operator_statuses, users)