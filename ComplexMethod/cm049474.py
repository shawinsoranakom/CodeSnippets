def tags(self, forum, tag_char='', filters='all', search='', **post):
        """Render a list of tags matching filters and search parameters.

        :param forum: Forum
        :param string tag_char: Only tags starting with a single character `tag_char`
        :param filters: One of 'all'|'followed'|'most_used'|'unused'.
          Can be combined with `search` and `tag_char`.
        :param string search: Search query using "forum_tags_only" `search_type`
        :param dict post: additional options passed to `_prepare_user_values`
        """
        if not isinstance(tag_char, str) or len(tag_char) > 1 or (tag_char and not tag_char.isalpha()):
            # So that further development does not miss this. Users shouldn't see it with normal usage.
            raise werkzeug.exceptions.BadRequest(_('Bad "tag_char" value "%(tag_char)s"', tag_char=tag_char))

        domain = [('forum_id', '=', forum.id), ('posts_count', '=' if filters == "unused" else '>', 0)]
        if filters == 'followed' and not request.env.user._is_public():
            domain = Domain.AND([domain, [('message_is_follower', '=', True)]])

        # Build tags result without using tag_char to build pager, then return tags matching it
        values = self._prepare_user_values(forum=forum, searches={'tags': True}, **post)
        tags = request.env["forum.tag"]

        order = 'posts_count DESC' if tag_char else 'name'

        if search:
            values.update(search=search)
            search_domain = domain if filters in ('all', 'followed') else None
            __, details, __ = request.website._search_with_fuzzy(
                'forum_tags_only', search, limit=None, order=order, options={'forum': forum, 'domain': search_domain},
            )
            tags = details[0].get('results', tags)

        if filters in ('unused', 'most_used'):
            filter_tags = forum.tag_most_used_ids if filters == 'most_used' else forum.tag_unused_ids
            tags = tags & filter_tags if tags else filter_tags
        elif filters in ('all', 'followed'):
            if not search:
                tags = request.env['forum.tag'].search(domain, limit=None, order=order)
        else:
            raise werkzeug.exceptions.BadRequest(_('Bad "filters" value "%(filters)s".', filters=filters))

        first_char_tag = forum._get_tags_first_char(tags=tags)
        first_char_list = [(t, t.lower()) for t in first_char_tag if t.isalnum()]
        first_char_list.insert(0, (_('All'), ''))
        if tag_char:
            tags = tags.filtered(lambda t: t.name.startswith((tag_char.lower(), tag_char.upper())))

        values.update({
            'active_char_tag': tag_char.lower(),
            'pager_tag_chars': first_char_list,
            'search_count': len(tags) if search else None,
            'tags': tags,
        })
        return request.render("website_forum.forum_index_tags", values)