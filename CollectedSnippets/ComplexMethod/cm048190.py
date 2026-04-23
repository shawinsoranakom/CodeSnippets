def _prepare_blog_values(self, blogs, blog=False, date_begin=False, date_end=False, tags=False, state=False, page=False, search=None, **post):
        """ Prepare all values to display the blogs index page or one specific blog"""
        BlogPost = request.env['blog.post']
        BlogTag = request.env['blog.tag']

        # prepare domain
        domain = request.website.website_domain()

        if blog:
            domain &= Domain('blog_id', '=', blog.id)

        if date_begin and date_end:
            domain &= Domain("post_date", ">=", date_begin) & Domain("post_date", "<=", date_end)
        active_tag_ids = tags and [request.env['ir.http']._unslug(tag)[1] for tag in tags.split(',')] or []
        active_tags = BlogTag
        if active_tag_ids:
            active_tags = BlogTag.browse(active_tag_ids).exists()
            fixed_tag_slug = ",".join(request.env['ir.http']._slug(t) for t in active_tags)
            if fixed_tag_slug != tags:
                path = request.httprequest.full_path
                new_url = path.replace("/tag/%s" % tags, fixed_tag_slug and "/tag/%s" % fixed_tag_slug or "", 1)
                if new_url != path:  # check that really replaced and avoid loop
                    return request.redirect(new_url, 301)
            domain &= Domain('tag_ids', 'in', active_tags.ids)

        if request.env.user.has_group('website.group_website_designer'):
            count_domain = domain & Domain("website_published", "=", True) & Domain("post_date", "<=", fields.Datetime.now())
            published_count = BlogPost.search_count(count_domain)
            unpublished_count = BlogPost.search_count(domain) - published_count

            if state == "published":
                domain &= Domain("website_published", "=", True) & Domain("post_date", "<=", fields.Datetime.now())
            elif state == "unpublished":
                domain &= Domain("website_published", "=", False) | ("post_date", ">", fields.Datetime.now())
        else:
            domain &= Domain("post_date", "<=", fields.Datetime.now())

        offset = (page - 1) * self._blog_post_per_page

        options = self._get_blog_post_search_options(
            blog=blog,
            active_tags=active_tags,
            date_begin=date_begin,
            date_end=date_end,
            state=state,
            **post
        )
        total, details, fuzzy_search_term = request.website._search_with_fuzzy("blog_posts_only", search,
            limit=page * self._blog_post_per_page, order="is_published desc, post_date desc, id asc", options=options)
        posts = details[0].get('results', BlogPost)
        posts = posts[offset:offset + self._blog_post_per_page]

        url_args = dict()
        if search:
            url_args["search"] = search

        if date_begin and date_end:
            url_args["date_begin"] = date_begin
            url_args["date_end"] = date_end

        pager = tools.lazy(lambda: request.website.pager(
            url=request.httprequest.path.partition('/page/')[0],
            total=total,
            page=page,
            step=self._blog_post_per_page,
            url_args=url_args,
        ))

        if not blogs:
            all_tags = request.env['blog.tag']
        else:
            all_tags = tools.lazy(lambda: blogs.all_tags(join=True) if not blog else blogs.all_tags().get(blog.id, request.env['blog.tag']))
        tag_category = tools.lazy(lambda: sorted(all_tags.mapped('category_id'), key=lambda category: category.name.upper()))
        other_tags = tools.lazy(lambda: sorted(all_tags.filtered(lambda x: not x.category_id), key=lambda tag: tag.name.upper()))
        nav_list = tools.lazy(lambda: self.nav_list(blog))
        # and avoid accessing related blogs one by one
        posts.blog_id

        return {
            'date_begin': date_begin,
            'date_end': date_end,
            'other_tags': other_tags,
            'tag_category': tag_category,
            'nav_list': nav_list,
            'tags_list': self.tags_list,
            'pager': pager,
            'posts': posts.with_prefetch(),
            'tag': tags,
            'active_tag_ids': active_tags.ids,
            'domain': domain,
            'state_info': state and {"state": state, "published": published_count, "unpublished": unpublished_count},
            'blogs': blogs,
            'blog': blog,
            'search': fuzzy_search_term or search,
            'search_count': total,
            'original_search': fuzzy_search_term and search,
        }