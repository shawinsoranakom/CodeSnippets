def create_slide(self, *args, **post):
        # check the size only when we upload a file.
        if post.get('binary_content'):
            file_size = len(post['binary_content']) * 3 / 4  # base64
            if (file_size / 1024.0 / 1024.0) > 25:
                return {'error': _('File is too big. File size cannot exceed 25MB')}

        values = dict((fname, post[fname]) for fname in self._get_valid_slide_post_values() if post.get(fname))

        # handle exception during creation of slide and sent error notification to the client
        # otherwise client slide create dialog box continue processing even server fail to create a slide
        try:
            channel = request.env['slide.channel'].browse(values['channel_id'])
            can_upload = channel.can_upload
            can_publish = channel.can_publish
        except UserError as e:
            _logger.error(e)
            return {'error': e.args[0]}
        else:
            if not can_upload:
                return {'error': _('You cannot upload on this channel.')}

        if post.get('duration'):
            # minutes to hours conversion
            values['completion_time'] = int(post['duration']) / 60

        category = False
        # handle creation of new categories on the fly
        if post.get('category_id'):
            category_id = post['category_id'][0]
            if category_id == 0:
                category = request.env['slide.slide'].create(self._get_new_slide_category_values(channel, post['category_id'][1]['name']))
                values['sequence'] = category.sequence + 1
            else:
                category = request.env['slide.slide'].browse(category_id)
                values.update({
                    'sequence': request.env['slide.slide'].browse(post['category_id'][0]).sequence + 1
                })

        # create slide itself
        try:
            values['user_id'] = request.env.uid
            slide = request.env['slide.slide'].sudo().create(values)
        except UserError as e:
            _logger.error(e)
            return {'error': e.args[0]}
        except Exception as e:
            _logger.error(e)
            return {'error': _('Internal server error, please try again later or contact administrator.\nHere is the error message: %s', e)}

        # ensure correct ordering by re sequencing slides in front-end (backend should be ok thanks to list view)
        channel._resequence_slides(slide, force_category=category)

        redirect_url = "/slides/slide/%s" % (slide.id)
        if slide.slide_category == 'article':
            redirect_url = request.env["website"].get_client_action_url(redirect_url, True)
        elif slide.slide_category == 'quiz':
            redirect_url += "?quiz_quick_create"
        elif channel.channel_type == "training":
            redirect_url = "/slides/%s" % (request.env['ir.http']._slug(channel))
        return {
            'url': redirect_url,
            'channel_type': channel.channel_type,
            'slide_id': slide.id,
            'category_id': slide.category_id
        }