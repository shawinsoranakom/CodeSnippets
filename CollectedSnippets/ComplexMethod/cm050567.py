def slides_channel_values(self, slide_category=None, slug_tags=None, my=0, page=None, page_size=12, **post):
        """ Home page displaying a list of courses displayed according to some
        criterion and search terms.

          :param string slide_category: if provided, filter the course to contain at
           least one slide of type 'slide_category'. Used notably to display courses
           with certifications;
          :param string slug_tags: if provided, filter the slide.channels having
            the tag(s) (in comma separated slugified form);
          :param bool my: if provided, filter the slide.channels for which the
           current user is a member of
          :param dict post: post parameters, including
          :param int|None page: The current page number. Set to None to disable pagination (default).
          :param int page_size: number of element per page

           * ``search``: filter on course description / name;
        """
        search_args = {
            'my': my,
            'slug_tags': slug_tags,
            'slide_category': slide_category,
            **post
        }
        options = self._get_slide_channel_search_options(**search_args)
        search = post.get('search')
        order = self._channel_order_by_criterion.get(post.get('sorting'))
        search_count, details, fuzzy_search_term = request.website._search_with_fuzzy(
            "slide_channels_only", search, limit=page * page_size if page else 1000, order=order, options=options)
        channels_all = details[0].get('results', request.env['slide.channel'])
        channels = channels_all[(page - 1) * page_size:page * page_size] if page else channels_all
        tag_groups = request.env['slide.channel.tag.group'].search(
            ['&', ('tag_ids', '!=', False), ('website_published', '=', True)])
        if slug_tags:
            search_tags = self._channel_search_tags_slug(slug_tags)
        elif post.get('tags'):
            search_tags = self._channel_search_tags_ids(post['tags'])
        else:
            search_tags = request.env['slide.channel.tag']

        render_values = self._slide_render_context_base()
        render_values.update(self._prepare_user_values(**post))
        render_values.update(self._slides_channel_user_values(
            compute_channels_my=not self._has_slide_channel_search(**search_args)))
        render_values.update({
            'channels': channels,
            'tag_groups': tag_groups,
            'search_term': fuzzy_search_term or search,
            'original_search': fuzzy_search_term and search,
            'search_slide_category': slide_category,
            'search_my': my,
            'search_tags': search_tags,
            'search_count': search_count,
            'top3_users': self._get_top3_users(),
            'slugify_tags': self._slugify_tags,
            'slide_query_url': QueryURL('/slides', ['tag']),
            'pager': request.website.pager(
                url=request.httprequest.path.partition('/page/')[0],
                url_args=request.httprequest.args.to_dict(),
                total=search_count,
                page=page,
                step=page_size,
                scope=3) if page else False,
        })

        return render_values