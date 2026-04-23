def extract_info(self, url, download=True, ie_key=None, extra_info=None,
                     process=True, force_generic_extractor=False):
        """
        Extract and return the information dictionary of the URL

        Arguments:
        @param url          URL to extract

        Keyword arguments:
        @param download     Whether to download videos
        @param process      Whether to resolve all unresolved references (URLs, playlist items).
                            Must be True for download to work
        @param ie_key       Use only the extractor with this key

        @param extra_info   Dictionary containing the extra values to add to the info (For internal use only)
        @force_generic_extractor  Force using the generic extractor (Deprecated; use ie_key='Generic')
        """

        if extra_info is None:
            extra_info = {}

        if not ie_key and force_generic_extractor:
            ie_key = 'Generic'

        if ie_key:
            ies = {ie_key: self._ies[ie_key]} if ie_key in self._ies else {}
        else:
            ies = self._ies

        for key, ie in ies.items():
            if not ie.suitable(url):
                continue

            if not ie.working():
                self.report_warning('The program functionality for this site has been marked as broken, '
                                    'and will probably not work.')

            temp_id = ie.get_temp_id(url)
            if temp_id is not None and self.in_download_archive({'id': temp_id, 'ie_key': key}):
                self.to_screen(f'[download] {self._format_screen(temp_id, self.Styles.ID)}: '
                               'has already been recorded in the archive')
                if self.params.get('break_on_existing', False):
                    raise ExistingVideoReached
                break
            return self.__extract_info(url, self.get_info_extractor(key), download, extra_info, process)
        else:
            extractors_restricted = self.params.get('allowed_extractors') not in (None, ['default'])
            self.report_error(f'No suitable extractor{format_field(ie_key, None, " (%s)")} found for URL {url}',
                              tb=False if extractors_restricted else None)