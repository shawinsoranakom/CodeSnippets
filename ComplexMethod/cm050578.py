def _compute_embed_code(self):
        request_base_url = request.httprequest.url_root if request else False
        for slide in self:
            base_url = request_base_url or slide.get_base_url()
            if base_url[-1] == '/':
                base_url = base_url[:-1]

            embed_code = False
            embed_code_external = False
            if slide.slide_category == 'video':
                if slide.video_source_type == 'youtube':
                    query_params = urls.url_parse(slide.video_url).query
                    query_params = query_params + '&theme=light' if query_params else 'theme=light'
                    embed_code = Markup('<iframe src="//www.youtube-nocookie.com/embed/%s?%s" allowFullScreen="true" frameborder="0" aria-label="%s"></iframe>') % (slide.youtube_id, query_params, _('YouTube'))
                elif slide.video_source_type == 'google_drive':
                    embed_code = Markup('<iframe src="//drive.google.com/file/d/%s/preview" allowFullScreen="true" frameborder="0" aria-label="%s"></iframe>') % (slide.google_drive_id, _('Google Drive'))
                elif slide.video_source_type == 'vimeo':
                    if '/' in slide.vimeo_id:
                        # in case of privacy 'with URL only', vimeo adds a token after the video ID
                        # the embed url needs to receive that token as a "h" parameter
                        [vimeo_id, vimeo_token] = slide.vimeo_id.split('/')
                        embed_code = Markup("""
                            <iframe src="https://player.vimeo.com/video/%s?h=%s&badge=0&amp;autopause=0&amp;player_id=0"
                                frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen aria-label="%s"></iframe>""") % (
                                vimeo_id, vimeo_token, _('Vimeo'))
                    else:
                        embed_code = Markup("""
                            <iframe src="https://player.vimeo.com/video/%s?badge=0&amp;autopause=0&amp;player_id=0"
                                frameborder="0" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen aria-label="%s"></iframe>""") % (slide.vimeo_id, _('Vimeo'))
            elif slide.slide_category in ['infographic', 'document'] and slide.source_type == 'external' and slide.google_drive_id:
                embed_code = Markup('<iframe src="//drive.google.com/file/d/%s/preview" allowFullScreen="true" frameborder="0" aria-label="%s"></iframe>') % (slide.google_drive_id, _('Google Drive'))
            elif slide.slide_category == 'document' and slide.source_type == 'local_file':
                slide_url = base_url + self.env['ir.http']._url_for('/slides/embed/%s?page=1' % slide.id)
                slide_url_external = base_url + self.env['ir.http']._url_for('/slides/embed_external/%s?page=1' % slide.id)
                base_embed_code = Markup('<iframe src="%s" class="o_wslides_iframe_viewer" allowFullScreen="true" height="%s" width="%s" frameborder="0" aria-label="%s"></iframe>')
                iframe_aria_label = _('Embed code')
                embed_code = base_embed_code % (slide_url, 315, 420, iframe_aria_label)
                embed_code_external = base_embed_code % (slide_url_external, 315, 420, iframe_aria_label)

            slide.embed_code = embed_code
            slide.embed_code_external = embed_code_external or embed_code