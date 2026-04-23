def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        search_fields = ['name']
        fetch_fields = ['id', 'name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }

        domain = website.website_domain()
        domain &= Domain('state', '=', 'active') & Domain('can_view', '=', True)
        include_answers = options.get('include_answers', False)
        if not include_answers:
            domain &= Domain('parent_id', '=', False)
        forum = options.get('forum')
        if forum:
            domain &= Domain('forum_id', '=', self.env['ir.http']._unslug(forum)[1])
        tags = options.get('tag')
        if tags:
            domain &= Domain('tag_ids', 'in', [self.env['ir.http']._unslug(tag)[1] for tag in tags.split(',')])
        filters = options.get('filters')
        if filters == 'unanswered':
            domain &= Domain('child_ids', '=', False)
        elif filters == 'solved':
            domain &= Domain('has_validated_answer', '=', True)
        elif filters == 'unsolved':
            domain &= Domain('has_validated_answer', '=', False)
        user = self.env.user
        my = options.get('my')
        create_uid = user.id if my == 'mine' else options.get('create_uid')
        if create_uid:
            domain &= Domain('create_uid', '=', create_uid)
        if my == 'followed':
            domain &= Domain('message_partner_ids', '=', user.partner_id.id)
        elif my == 'tagged':
            domain &= Domain('tag_ids.message_partner_ids', '=', user.partner_id.id)
        elif my == 'favourites':
            domain &= Domain('favourite_ids', '=', user.id)
        elif my == 'upvoted':
            domain &= Domain('vote_ids.user_id', '=', user.id)

        # 'sorting' from the form's "Order by" overrides order during auto-completion
        order = options.get('sorting', order)
        if 'is_published' in order:
            parts = [part for part in order.split(',') if 'is_published' not in part]
            order = ','.join(parts)

        if with_description:
            search_fields.append('content')
            fetch_fields.append('content')
            mapping['description'] = {'name': 'content', 'type': 'text', 'html': True, 'match': True}
        if with_date:
            fetch_fields.append('write_date')
            mapping['detail'] = {'name': 'date', 'type': 'html'}
        return {
            'model': 'forum.post',
            'base_domain': [domain],
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-comment-o',
            'order': order,
        }