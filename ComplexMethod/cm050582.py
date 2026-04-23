def create(self, vals_list):
        channel_ids = [vals['channel_id'] for vals in vals_list]
        can_publish_channel_ids = self.env['slide.channel'].browse(channel_ids).filtered(lambda c: c.can_publish).ids
        for vals in vals_list:
            # Do not publish slide if user has not publisher rights
            if vals['channel_id'] not in can_publish_channel_ids:
                # 'website_published' is handled by mixin
                vals['date_published'] = False

            if vals.get('is_category'):
                vals['is_preview'] = True
                vals['is_published'] = True
            if vals.get('is_published') and not vals.get('date_published'):
                vals['date_published'] = datetime.datetime.now()

        slides = super().create(vals_list)

        for slide, vals in zip(slides, vals_list):
            # avoid fetching external metadata when installing the module (i.e. for demo data)
            # we also support a context key if you don't want to fetch the metadata when creating a slide
            if any(vals.get(url_param) for url_param in ['url', 'video_url', 'document_google_url', 'image_google_url']) \
               and not self.env.context.get('install_mode') \
               and not self.env.context.get('website_slides_skip_fetch_metadata'):
                slide_metadata, _error = slide._fetch_external_metadata()
                if slide_metadata:
                    # only update keys that are not set in the incoming vals
                    slide.update({key: value for key, value in slide_metadata.items() if key not in vals.keys()})

            if 'completion_time' not in vals:
                slide._on_change_document_binary_content()

            if slide.is_published and not slide.is_category:
                slide._post_publication()
                slide.channel_id.channel_partner_ids._recompute_completion()
        return slides