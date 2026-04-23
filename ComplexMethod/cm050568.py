def channel(self, channel=False, channel_id=False, category=None, category_id=False, tag=None, page=1, slide_category=None, uncategorized=False, sorting=None, search=None, **kw):
        """ Will return the rendered page of a course, with optional parameters allowing customization:

        :param channel: slide.channel to be rendered.
        :param channel_id: id of the rendered channel. (*)
        :param category: slide.slide (should be a category). Filter contents to those
            below this category (= section).
        :param category_id: id of the desired slide.slide category. (*)
        :param tag: slide.tag used to filter contents.
        :param slide_category: one of the values of linked selection field.
            Filter to this category of slides (video, article...)
        :param uncategorized: To set to True to access all slides outside of any slide.slide category.
        :param sorting: string defining the way to sort contents. ('most_voted', ...)
        :param search: string of the user search in the search bar.
        :param kw.invite_partner_id: id of the invited partner. (**)
        :param kw.invite_hash: string hash based on course and partner. (**)

        (*) Should be used for preview of invited attendees only. A 403 error could occur when using
            channel and category, if their access to models is denied. The generic shared course link
            uses channel_id as well, for the same reason.
        (**) Those are used to check and give invited attendees the access to the course and
            allow them browing its list of contents.
        """
        invite_partner_id = int(kw['invite_partner_id']) if kw.get('invite_partner_id') else False
        invite_hash = kw.get('invite_hash')
        valid_invite_values = {}

        # Invitation data processing
        if request.website.is_public_user() and invite_partner_id and invite_hash and channel_id and not channel:
            valid_invite_values = self._get_channel_values_from_invite(channel_id, invite_hash, invite_partner_id)
            if valid_invite_values.get('invite_preview'):
                channel = valid_invite_values.get('invite_channel')
                valid_invite_values['pager_args'] = {
                    'invite_hash': invite_hash,
                    'invite_partner_id': invite_partner_id
                }

        if channel_id < 0:
            # the string part of the channel "slugification" can be blank
            # meaning it can be "/slides/taking-care-of-trees-2" OR just "/slides/-2" if the first part is blank
            # as we use a IntConverter on the route definition, this will pick up a negative ID
            # (the IntConverter is necessary as we want a custom page in case the user can't access the course)
            channel_id = abs(channel_id)

        # Check access rights
        if channel_id and not channel:
            channel = request.env['slide.channel'].browse(channel_id).exists()
            if not channel:
                return self._redirect_to_slides_main('no_channel')
        if not channel.has_access('read'):
            return self._redirect_to_slides_main('no_rights')

        if category_id and not category:
            category = channel.slide_category_ids.filtered(lambda category: category.id == category_id)

        domain = self._get_channel_slides_base_domain(channel)
        pager_url = "/slides/%s" % (channel.id)
        pager_args = valid_invite_values.get('pager_args', {})
        slide_categories = dict(request.env['slide.slide']._fields['slide_category']._description_selection(request.env))

        if search:
            domain &= (
                Domain('name', 'ilike', search)
                | Domain('description', 'ilike', search)
                | Domain('html_content', 'ilike', search)
            )
            pager_args['search'] = search
        else:
            if category:
                domain &= Domain('category_id', '=', category.id)
                pager_url += "/category/%s" % category.id
            elif tag:
                domain &= Domain('tag_ids', '=', tag.id)
                pager_url += "/tag/%s" % tag.id
            if uncategorized:
                domain &= Domain('category_id', '=', False)
                pager_args['uncategorized'] = 1
            elif slide_category:
                domain &= Domain('slide_category', '=', slide_category)
                pager_url += "?slide_category=%s" % slide_category

        # sorting criterion
        if channel.channel_type == 'documentation':
            default_sorting = 'latest' if channel.promote_strategy in ['specific', 'none', False] else channel.promote_strategy
            actual_sorting = sorting if sorting and sorting in request.env['slide.slide']._order_by_strategy else default_sorting
        else:
            actual_sorting = 'sequence'
        order = request.env['slide.slide']._order_by_strategy[actual_sorting]
        pager_args['sorting'] = actual_sorting

        slide_count = request.env['slide.slide'].sudo().search_count(domain)
        page_count = math.ceil(slide_count / self._slides_per_page)
        pager = request.website.pager(url=pager_url, total=slide_count, page=page,
                                      step=self._slides_per_page, url_args=pager_args,
                                      scope=page_count if page_count < self._pager_max_pages else self._pager_max_pages)

        query_string = None
        if category:
            query_string = "?search_category=%s" % category.id
        elif tag:
            query_string = "?search_tag=%s" % tag.id
        elif slide_category:
            query_string = "?search_slide_category=%s" % slide_category
        elif uncategorized:
            query_string = "?search_uncategorized=1"

        errors = {'access_error': False}
        if request.params.get('access_error') == 'course_content' and request.params.get('access_error_slide_id'):
            # Access are re-verified to support use case where the user refresh the page after an update of their access
            user_slide_authorization = self._get_user_slide_authorization(int(request.params.get('access_error_slide_id')))
            if user_slide_authorization['status'] == 'not_authorized':
                errors.update({
                    'access_error': 'course_content',
                    'access_error_content_name': request.params.get('access_error_slide_name'),
                })

        render_values = self._slide_render_context_base()
        render_values.update({
            'channel': channel,
            'main_object': channel,
            'active_tab': kw.get('active_tab', 'home'),
            # search
            'search_category': category,
            'search_tag': tag,
            'search_slide_category': slide_category,
            'search_uncategorized': uncategorized,
            'query_string': query_string,
            'slide_categories': slide_categories,
            'sorting': actual_sorting,
            'search': search,
            # display data
            'pager': pager,
            'slide_count': slide_count,
            # display upload modal
            'enable_slide_upload': kw.get('enable_slide_upload', False),
            # invitation data
            'invite_hash': invite_hash,
            'invite_partner_id': invite_partner_id,
            'invite_preview': valid_invite_values.get('invite_preview'),
            'is_partner_without_user': valid_invite_values.get('is_partner_without_user'),
            ** errors,
            ** self._slide_channel_prepare_review_values(channel),
        })

        # fetch slides and handle uncategorized slides; done as sudo because we want to display all
        # of them but unreachable ones won't be clickable (+ slide controller will crash anyway)
        # documentation mode may display less slides than content by category but overhead of
        # computation is reasonable
        if channel.promote_strategy == 'specific':
            render_values['slide_promoted'] = channel.sudo().promoted_slide_id
        else:
            render_values['slide_promoted'] = request.env['slide.slide'].sudo().search(domain, limit=1, order=order)

        limit_category_data = False
        if channel.channel_type == 'documentation':
            if category or uncategorized:
                limit_category_data = self._slides_per_page
            else:
                limit_category_data = self._slides_per_category

        render_values['category_data'] = channel._get_categorized_slides(
            domain, order,
            force_void=not category,
            limit=limit_category_data,
            offset=pager['offset'])
        render_values['channel_progress'] = self._get_channel_progress(channel, include_quiz=True)

        # for sys admins: prepare data to install directly modules from eLearning when
        # uploading slides. Currently supporting only survey, because why not.
        if request.env.user.has_group('base.group_system'):
            module = request.env.ref('base.module_survey')
            if module.state != 'installed':
                render_values['modules_to_install'] = json.dumps([{
                    'id': module.id,
                    'name': module.shortdesc,
                    'motivational': _('Want to test and certify your students?'),
                    'default_slide_category': 'certification',
                }])

        render_values = self._prepare_additional_channel_values(render_values, **kw)
        return request.render('website_slides.course_main', render_values)