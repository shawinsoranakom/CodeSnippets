def process_ie_result(self, ie_result, download=True, extra_info=None):
        """
        Take the result of the ie(may be modified) and resolve all unresolved
        references (URLs, playlist items).

        It will also download the videos if 'download'.
        Returns the resolved ie_result.
        """
        if extra_info is None:
            extra_info = {}
        result_type = ie_result.get('_type', 'video')

        if result_type in ('url', 'url_transparent'):
            ie_result['url'] = sanitize_url(
                ie_result['url'], scheme='http' if self.params.get('prefer_insecure') else 'https')
            if ie_result.get('original_url') and not extra_info.get('original_url'):
                extra_info = {'original_url': ie_result['original_url'], **extra_info}

            extract_flat = self.params.get('extract_flat', False)
            if ((extract_flat == 'in_playlist' and 'playlist' in extra_info)
                    or extract_flat is True):
                info_copy = ie_result.copy()
                ie = try_get(ie_result.get('ie_key'), self.get_info_extractor)
                if ie and not ie_result.get('id'):
                    info_copy['id'] = ie.get_temp_id(ie_result['url'])
                self.add_default_extra_info(info_copy, ie, ie_result['url'])
                self.add_extra_info(info_copy, extra_info)
                info_copy, _ = self.pre_process(info_copy)
                self._fill_common_fields(info_copy, False)
                self.__forced_printings(info_copy)
                self._raise_pending_errors(info_copy)
                if self.params.get('force_write_download_archive', False):
                    self.record_download_archive(info_copy)
                return ie_result

        if result_type == 'video':
            self.add_extra_info(ie_result, extra_info)
            ie_result = self.process_video_result(ie_result, download=download)
            self._raise_pending_errors(ie_result)
            additional_urls = (ie_result or {}).get('additional_urls')
            if additional_urls:
                # TODO: Improve MetadataParserPP to allow setting a list
                if isinstance(additional_urls, str):
                    additional_urls = [additional_urls]
                self.to_screen(
                    '[info] {}: {} additional URL(s) requested'.format(ie_result['id'], len(additional_urls)))
                self.write_debug('Additional URLs: "{}"'.format('", "'.join(additional_urls)))
                ie_result['additional_entries'] = [
                    self.extract_info(
                        url, download, extra_info=extra_info,
                        force_generic_extractor=self.params.get('force_generic_extractor'))
                    for url in additional_urls
                ]
            return ie_result
        elif result_type == 'url':
            # We have to add extra_info to the results because it may be
            # contained in a playlist
            return self.extract_info(
                ie_result['url'], download,
                ie_key=ie_result.get('ie_key'),
                extra_info=extra_info)
        elif result_type == 'url_transparent':
            # Use the information from the embedding page
            info = self.extract_info(
                ie_result['url'], ie_key=ie_result.get('ie_key'),
                extra_info=extra_info, download=False, process=False)

            # extract_info may return None when ignoreerrors is enabled and
            # extraction failed with an error, don't crash and return early
            # in this case
            if not info:
                return info

            exempted_fields = {'_type', 'url', 'ie_key'}
            if not ie_result.get('section_end') and ie_result.get('section_start') is None:
                # For video clips, the id etc of the clip extractor should be used
                exempted_fields |= {'id', 'extractor', 'extractor_key'}

            new_result = info.copy()
            new_result.update(filter_dict(ie_result, lambda k, v: v is not None and k not in exempted_fields))

            # Extracted info may not be a video result (i.e.
            # info.get('_type', 'video') != video) but rather an url or
            # url_transparent. In such cases outer metadata (from ie_result)
            # should be propagated to inner one (info). For this to happen
            # _type of info should be overridden with url_transparent. This
            # fixes issue from https://github.com/ytdl-org/youtube-dl/pull/11163.
            if new_result.get('_type') == 'url':
                new_result['_type'] = 'url_transparent'

            return self.process_ie_result(
                new_result, download=download, extra_info=extra_info)
        elif result_type in ('playlist', 'multi_video'):
            # Protect from infinite recursion due to recursively nested playlists
            # (see https://github.com/ytdl-org/youtube-dl/issues/27833)
            webpage_url = ie_result.get('webpage_url')  # Playlists maynot have webpage_url
            if webpage_url and webpage_url in self._playlist_urls:
                self.to_screen(
                    '[download] Skipping already downloaded playlist: {}'.format(
                        ie_result.get('title')) or ie_result.get('id'))
                return

            self._playlist_level += 1
            self._playlist_urls.add(webpage_url)
            self._fill_common_fields(ie_result, False)
            self._sanitize_thumbnails(ie_result)
            try:
                return self.__process_playlist(ie_result, download)
            finally:
                self._playlist_level -= 1
                if not self._playlist_level:
                    self._playlist_urls.clear()
        elif result_type == 'compat_list':
            self.report_warning(
                'Extractor {} returned a compat_list result. '
                'It needs to be updated.'.format(ie_result.get('extractor')))

            def _fixup(r):
                self.add_extra_info(r, {
                    'extractor': ie_result['extractor'],
                    'webpage_url': ie_result['webpage_url'],
                    'webpage_url_basename': url_basename(ie_result['webpage_url']),
                    'webpage_url_domain': get_domain(ie_result['webpage_url']),
                    'extractor_key': ie_result['extractor_key'],
                })
                return r
            ie_result['entries'] = [
                self.process_ie_result(_fixup(r), download, extra_info)
                for r in ie_result['entries']
            ]
            return ie_result
        else:
            raise Exception(f'Invalid result type: {result_type}')