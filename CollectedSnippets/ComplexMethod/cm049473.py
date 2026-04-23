def questions(self, forum=None, tag=None, page=1, filters='all', my=None, sorting=None, search='', create_uid=False, include_answers=False, **post):
        Post = request.env['forum.post']

        author = request.env['res.users'].browse(int(create_uid))

        if author == request.env.user:
            my = 'mine'
        if sorting:
            # check that sorting is valid
            # retro-compatibility for V8 and google links
            try:
                sorting = werkzeug.urls.url_unquote_plus(sorting)
                Post._order_to_sql(sorting, Post._search([], bypass_access=True))
            except (UserError, ValueError):
                sorting = False

        if not sorting:
            sorting = forum.default_order if forum else 'last_activity_date desc'

        options = self._get_forum_post_search_options(
            forum=forum,
            tag=tag,
            filters=filters,
            my=my,
            create_uid=author.id,
            include_answers=include_answers,
            my_profile=request.env.user == author,
            **post
        )

        slug = request.env['ir.http']._slug
        question_count, details, fuzzy_search_term = request.website._search_with_fuzzy(
            "forum_posts_only", search, limit=page * self._post_per_page, order=sorting, options=options)
        question_ids = details[0].get('results', Post)
        question_ids = question_ids[(page - 1) * self._post_per_page:page * self._post_per_page]

        if not forum:
            url = '/forum/all'
        elif tag:
            url = f'/forum/{slug(forum)}/tag/{slug(tag)}/questions'
        else:
            url = f'/forum/{slug(forum)}'

        url_args = {'sorting': sorting}

        for name, value in zip(['filters', 'search', 'my'], [filters, search, my]):
            if value:
                url_args[name] = value

        pager = tools.lazy(lambda: request.website.pager(
            url=url, total=question_count, page=page, step=self._post_per_page,
            scope=5, url_args=url_args))

        values = self._prepare_user_values(forum=forum, searches=post)
        values.update({
            'author': author,
            'edit_in_backend': True,
            'question_ids': question_ids,
            'question_count': question_count,
            'search_count': question_count,
            'pager': pager,
            'tag': tag,
            'filters': filters,
            'my': my,
            'sorting': sorting,
            'search': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
        })

        if forum or tag:
            values['main_object'] = tag or forum

        return request.render("website_forum.forum_index", values)