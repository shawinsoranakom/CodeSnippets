def view_all_users_page(self, page=1, **kwargs):
        User = request.env['res.users']
        dom = [('karma', '>', 1), ('website_published', '=', True)]

        # Searches
        search_term = kwargs.get('search')
        group_by = kwargs.get('group_by', False)
        render_values = {
            'search': search_term,
            'group_by': group_by or 'all',
        }
        if search_term:
            dom = Domain.AND([['|', ('name', 'ilike', search_term), ('partner_id.commercial_company_name', 'ilike', search_term)], dom])

        user_count = User.sudo().search_count(dom)
        my_user = request.env.user
        current_user_values = False
        if user_count:
            page_count = math.ceil(user_count / self._users_per_page)
            pager = request.website.pager(url="/profile/users", total=user_count, page=page, step=self._users_per_page,
                                          scope=page_count if page_count < self._pager_max_pages else self._pager_max_pages,
                                          url_args=kwargs)

            # Get karma position for users (only website_published)
            position_domain = [('karma', '>', 1), ('website_published', '=', True)]

            if group_by:
                to_date = fields.Date.today()
                if group_by == 'week':
                    from_date = to_date - relativedelta(weeks=1)
                elif group_by == 'month':
                    from_date = to_date - relativedelta(months=1)
                else:
                    from_date = None
                user_ids = request.env['res.users']._get_user_ids_ranked_by_karma(
                    dom,
                    from_date=from_date,
                    to_date=to_date,
                    limit=self._users_per_page,
                    offset=pager['offset'],
                )
                users = User.sudo().browse(user_ids)
            else:
                users = User.sudo().search(
                    dom,
                    limit=self._users_per_page,
                    offset=pager['offset'],
                    order='karma DESC, id DESC',
                )

            user_values = self._prepare_all_users_values(users)
            position_map = self._get_position_map(position_domain, users, group_by)

            max_position = max([user_data['karma_position'] for user_data in position_map.values()], default=1)
            for user in user_values:
                user_data = position_map.get(user['id'], dict())
                user['position'] = user_data.get('karma_position', max_position + 1)
                user['karma_gain'] = user_data.get('karma_gain_total', 0)
            user_values.sort(key=itemgetter('position'))

            if my_user.website_published and my_user.karma and my_user.id not in users.ids:
                # Need to keep the dom to search only for users that appear in the ranking page
                current_user = User.sudo().search(Domain.AND([[('id', '=', my_user.id)], dom]))
                if current_user:
                    current_user_values = self._prepare_all_users_values(current_user)[0]

                    user_data = self._get_position_map(position_domain, current_user, group_by).get(current_user.id, {})
                    current_user_values['position'] = user_data.get('karma_position', 0)
                    current_user_values['karma_gain'] = user_data.get('karma_gain_total', 0)

        else:
            user_values = []
            pager = {'page_count': 0}
        render_values.update({
            'top3_users': user_values[:3] if not search_term and page == 1 else [],
            'users': user_values,
            'my_user': current_user_values,
            'pager': pager,
            **self._prepare_url_from_info(),
        })
        return request.render("website_profile.users_page_main", render_values)