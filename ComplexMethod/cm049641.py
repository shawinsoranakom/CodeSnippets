def _get_response_raw(self, request) -> http.Response | None:
        """ Returns the raw response associated with the current request.
        This method is called by `_get_response_cached`, which handles caching
        the result. It is also called directly by `_get_response` if
        `_allow_to_use_cache` returns False.
        """
        req_page = request.httprequest.path

        # fetch all prefetchable fields to get all data at once. If we use the
        # default fetch(), another query is necessary to get the page fields
        # like 'website_meta'.
        fields_to_fetch = [name for name, field in self._fields.items() if field.prefetch]
        self.fetch(fields_to_fetch)

        fields_to_fetch = [name for name, field in self.view_id._fields.items() if field.prefetch]
        self.view_id.fetch(fields_to_fetch)

        if (
            (self.env.user.has_group('website.group_website_designer') or self.is_visible)
            and (
                # If a generic page (niche case) has been COWed and that COWed
                # page received a URL change, it should not let you access the
                # generic page anymore, despite having a different URL.
                self.website_id
                or self.view_id.id == self.env['ir.ui.view'].with_context(website_id=request.website.id)._get_cached_template_info(self.view_id.key)['id']
            )
        ):
            _, ext = os.path.splitext(req_page)
            response = request.render(self.view_id.id, {
                'main_object': self,
            }, mimetype=EXTENSION_TO_WEB_MIMETYPES.get(ext, 'text/html'))
            response.time = time.time()
            return response

        return None