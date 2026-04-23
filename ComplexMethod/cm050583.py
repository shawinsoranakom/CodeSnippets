def write(self, vals):
        values = vals
        if values.get('is_category'):
            values['is_preview'] = True
            values['is_published'] = True

        # if the slide type is changed, remove incompatible url or html_content
        # done here to satisfy the SQL constraint
        # using a stored-computed field in place does not work
        if 'slide_category' in values:
            if values['slide_category'] == 'article':
                values = {'url': False, **values}
            elif values['slide_category'] != 'article':
                values = {'html_content': False, **values}

        res = super().write(values)

        if values.get('is_published'):
            self.date_published = datetime.datetime.now()
            self._post_publication()

        # avoid fetching external metadata when installing the module (i.e. for demo data)
        # we also support a context key if you don't want to fetch the metadata when modifying a slide
        if any(values.get(url_param) for url_param in ['url', 'video_url', 'document_google_url', 'image_google_url']) \
           and not self.env.context.get('install_mode') \
           and not self.env.context.get('website_slides_skip_fetch_metadata'):
            slide_metadata, _error = self._fetch_external_metadata()
            if slide_metadata:
                # only update keys that are not set in the incoming values and for which we don't have a value yet
                self.update({
                    key: value
                    for key, value in slide_metadata.items()
                    if key not in values.keys() and not any(slide[key] for slide in self)
                })

        if 'is_published' in values or 'active' in values:
            # archiving a channel unpublishes its slides
            self.filtered(lambda slide: not slide.active and not slide.is_category and slide.is_published).is_published = False
            # recompute the completion for all partners of the channel
            self.channel_id.channel_partner_ids._recompute_completion()

        return res