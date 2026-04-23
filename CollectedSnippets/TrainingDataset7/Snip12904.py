def _mark_post_parse_error(self):
        self._post = QueryDict()
        self._files = MultiValueDict()