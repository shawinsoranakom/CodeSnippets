def _post_processing_att(self, tagName, atts):
        if atts.get('data-no-post-process'):
            return atts

        atts = super()._post_processing_att(tagName, atts)

        website = ir_http.get_request_website()
        if not website and self.env.context.get('website_id'):
            website = self.env['website'].browse(self.env.context['website_id'])
        if website and tagName == 'img' and 'loading' not in atts:
            atts['loading'] = 'lazy'  # default is auto

        if self.env.context.get('inherit_branding') or self.env.context.get('rendering_bundle') or \
           self.env.context.get('edit_translations') or self.env.context.get('debug') or (request and request.session.debug):
            return atts

        if not website:
            return atts

        if website._should_remove_third_party_trackers():
            website._remove_third_party_trackers(tagName, atts, ['domains', 'classes'])

        name = self.URL_ATTRS.get(tagName)
        if request:
            value = atts.get(name) if name else None
            if value not in (None, False, ()):
                atts[name] = self.env['ir.http']._url_for(str(value))

            # Adapt background-image URL in the same way as image src.
            atts = self._adapt_style_background_image(atts, self.env['ir.http']._url_for)

        if not website.cdn_activated:
            return atts

        data_name = f'data-{name}'
        if name and (name in atts or data_name in atts):
            atts = OrderedDict(atts)
            if name in atts and atts[name] not in (False, None, ()):
                atts[name] = website.get_cdn_url(atts[name])
            if data_name in atts and atts[data_name] not in (False, None, ()):
                atts[data_name] = website.get_cdn_url(atts[data_name])
        atts = self._adapt_style_background_image(atts, website.get_cdn_url)

        return atts