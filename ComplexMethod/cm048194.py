def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        blog = options.get('blog')
        tags = options.get('tag')
        date_begin = options.get('date_begin')
        date_end = options.get('date_end')
        state = options.get('state')
        domain = [website.website_domain()]
        if blog:
            domain.append([('blog_id', '=', self.env['ir.http']._unslug(blog)[1])])
        if tags:
            active_tag_ids = [self.env['ir.http']._unslug(tag)[1] for tag in tags.split(',')] or []
            if active_tag_ids:
                domain.append([('tag_ids', 'in', active_tag_ids)])
        if date_begin and date_end:
            domain.append([("post_date", ">=", date_begin), ("post_date", "<=", date_end)])
        if self.env.user.has_group('website.group_website_designer'):
            if state == "published":
                domain.append([("website_published", "=", True), ("post_date", "<=", fields.Datetime.now())])
            elif state == "unpublished":
                domain.append(['|', ("website_published", "=", False), ("post_date", ">", fields.Datetime.now())])
        else:
            domain.append([("post_date", "<=", fields.Datetime.now())])
        search_fields = ['name', 'author_name']
        def search_in_tags(env, search_term):
            tags_like_search = env['blog.tag'].search([('name', 'ilike', search_term)])
            return [('tag_ids', 'in', tags_like_search.ids)]
        fetch_fields = ['name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }
        if with_description:
            search_fields.append('content')
            fetch_fields.append('content')
            mapping['description'] = {'name': 'content', 'type': 'text', 'html': True, 'match': True}
        if with_date:
            fetch_fields.append('published_date')
            mapping['detail'] = {'name': 'published_date', 'type': 'date'}
        return {
            'model': 'blog.post',
            'base_domain': domain,
            'search_fields': search_fields,
            'search_extra': search_in_tags,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-rss',
        }