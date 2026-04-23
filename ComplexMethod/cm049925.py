def get_activity_data(self, res_model, domain, limit=None, offset=0, fetch_done=False):
        """ Get aggregate data about records and their activities.

        The goal is to fetch and compute aggregated data about records and their
        activities to display them in the activity views and the chatter. For example,
        the activity view displays it as a table with columns and rows being respectively
        the activity_types and the activity_res_ids, and the grouped_activities being the
        table entries with the aggregated data.

        :param str res_model: model of the records to fetch
        :param list domain: record search domain
        :param int limit: maximum number of records to fetch
        :param int offset: offset of the first record to fetch
        :param bool fetch_done: determines if "done" activities are integrated in the
            aggregated data or not.
        :returns: {'activity_types': dict of activity type info
                            {id: int, name: str, mail_template: list of {id:int, name:str}}
                       'activity_res_ids': list<int> of record id ordered by closest date
                            (deadline for ongoing activities, and done date for done activities)
                       'grouped_activities': dict<dict>
                            res_id -> activity_type_id -> aggregated info as:
                                count_by_state dict: mapping state to count (ex.: 'planned': 2)
                                ids list: activity ids for the res_id and activity_type_id
                                reporting_date str: aggregated date of the related activities as
                                    oldest deadline of ongoing activities if there are any
                                    or most recent date done of completed activities
                                state dict: aggregated state of the related activities
                                user_assigned_ids list: activity responsible id ordered
                                    by closest deadline of the related activities
                                attachments_info: dict with information about the attachments
                                    {'count': int, 'most_recent_id': int, 'most_recent_name': str}
                       }
        :rtype: dict
        """
        user_tz = self.user_id.sudo().tz
        DocModel = self.env[res_model]
        Activity = self.env['mail.activity']

        # 1. Retrieve all ongoing and completed activities according to the parameters
        activity_types = self.env['mail.activity.type'].search([('res_model', 'in', (res_model, False))])
        activity_domain = [('res_model', '=', res_model)]
        is_filtered = domain or limit or offset
        if is_filtered:
            activity_domain.append(('res_id', 'in', DocModel._search(domain or [], offset, limit, DocModel._order) if is_filtered else []))
        all_activities = Activity.with_context(active_test=not fetch_done).search(
            activity_domain, order='date_done DESC, date_deadline ASC')
        all_ongoing = all_activities.filtered('active')
        all_completed = all_activities.filtered(lambda act: not act.active)

        # 2. Get attachment of completed activities
        if all_completed:
            attachment_ids = all_completed.attachment_ids.ids
            attachments_by_id = {
                a['id']: a
                for a in self.env['ir.attachment'].search_read([['id', 'in', attachment_ids]], ['create_date', 'name'])
            } if attachment_ids else {}
        else:
            attachments_by_id = {}

        # 3. Group activities per records and activity type
        grouped_completed = {group: Activity.browse([v.id for v in values])
                             for group, values in groupby(all_completed, key=lambda a: (a.res_id, a.activity_type_id))}
        grouped_ongoing = {group: Activity.browse([v.id for v in values])
                           for group, values in groupby(all_ongoing, key=lambda a: (a.res_id, a.activity_type_id))}

        # 4. Filter out unreadable records
        res_id_type_tuples = grouped_ongoing.keys() | grouped_completed.keys()
        if not is_filtered:
            filtered = set(DocModel.search([('id', 'in', [r[0] for r in res_id_type_tuples])]).ids)
            res_id_type_tuples = list(filter(lambda r: r[0] in filtered, res_id_type_tuples))

        # 5. Format data
        res_id_to_date_done = {}
        res_id_to_deadline = {}
        grouped_activities = defaultdict(dict)
        for res_id_tuple in res_id_type_tuples:
            res_id, activity_type_id = res_id_tuple
            ongoing = grouped_ongoing.get(res_id_tuple, Activity)
            completed = grouped_completed.get(res_id_tuple, Activity)
            activities = ongoing | completed

            # As completed is sorted on date_done DESC, we take here the max date_done
            date_done = completed and completed[0].date_done
            # As ongoing is sorted on date_deadline ASC, we take here the min date_deadline
            date_deadline = ongoing and ongoing[0].date_deadline
            if date_deadline and (res_id not in res_id_to_deadline or date_deadline < res_id_to_deadline[res_id]):
                res_id_to_deadline[res_id] = date_deadline
            if date_done and (res_id not in res_id_to_date_done or date_done > res_id_to_date_done[res_id]):
                res_id_to_date_done[res_id] = date_done
            # As ongoing is sorted on date_deadline, we get assignees on activity with oldest deadline first
            user_assigned_ids = ongoing.user_id.ids
            attachments = [attachments_by_id[attach.id] for attach in completed.attachment_ids]

            grouped_activities[res_id][activity_type_id.id] = {
                'count_by_state': dict(Counter(
                    self._compute_state_from_date(act.date_deadline, user_tz) if act.active else 'done'
                    for act in activities)),
                'ids': activities.ids,
                'reporting_date': ongoing and date_deadline or date_done or None,
                'state': self._compute_state_from_date(date_deadline, user_tz) if ongoing else 'done',
                'user_assigned_ids': user_assigned_ids,
                'summaries': [act.summary if act.summary else '' for act in activities],
            }
            if attachments:
                most_recent_attachment = max(attachments, key=lambda a: (a['create_date'], a['id']))
                grouped_activities[res_id][activity_type_id.id]['attachments_info'] = {
                    'most_recent_id': most_recent_attachment['id'],
                    'most_recent_name': most_recent_attachment['name'],
                    'count': len(attachments),
                }

        # Get record ids ordered by oldest deadline (urgent one first)
        ongoing_res_ids = sorted(res_id_to_deadline, key=lambda item: res_id_to_deadline[item])
        # Get record ids with only completed activities ordered by date done reversed (most recently done first)
        completed_res_ids = [
            res_id for res_id in sorted(
                res_id_to_date_done, key=lambda item: res_id_to_date_done[item], reverse=True
            ) if res_id not in res_id_to_deadline
        ]
        return {
            'activity_res_ids': ongoing_res_ids + completed_res_ids,
            'activity_types': [
                {
                    'id': activity_type.id,
                    'name': activity_type.name,
                    'template_ids': [
                        {'id': mail_template_id.id, 'name': mail_template_id.name}
                        for mail_template_id in activity_type.mail_template_ids
                    ],
                }
                for activity_type in activity_types
            ],
            'grouped_activities': grouped_activities,
        }