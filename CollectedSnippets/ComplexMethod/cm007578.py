def _real_extract(self, url):
        lecture_slug, explicit_part_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, lecture_slug)

        cfg = self._parse_json(self._search_regex(
            [r'cfg\s*:\s*({.+?})\s*,\s*[\da-zA-Z_]+\s*:\s*\(?\s*function',
             r'cfg\s*:\s*({[^}]+})'],
            webpage, 'cfg'), lecture_slug, js_to_json)

        lecture_id = compat_str(cfg['obj_id'])

        base_url = self._proto_relative_url(cfg['livepipe'], 'http:')

        try:
            lecture_data = self._download_json(
                '%s/site/api/lecture/%s?format=json' % (base_url, lecture_id),
                lecture_id)['lecture'][0]
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                msg = self._parse_json(
                    e.cause.read().decode('utf-8'), lecture_id)
                raise ExtractorError(msg['detail'], expected=True)
            raise

        lecture_info = {
            'id': lecture_id,
            'display_id': lecture_slug,
            'title': lecture_data['title'],
            'timestamp': parse_iso8601(lecture_data.get('time')),
            'description': lecture_data.get('description_wiki'),
            'thumbnail': lecture_data.get('thumb'),
        }

        playlist_entries = []
        lecture_type = lecture_data.get('type')
        parts = [compat_str(video) for video in cfg.get('videos', [])]
        if parts:
            multipart = len(parts) > 1

            def extract_part(part_id):
                smil_url = '%s/%s/video/%s/smil.xml' % (base_url, lecture_slug, part_id)
                smil = self._download_smil(smil_url, lecture_id)
                info = self._parse_smil(smil, smil_url, lecture_id)
                self._sort_formats(info['formats'])
                info['id'] = lecture_id if not multipart else '%s_part%s' % (lecture_id, part_id)
                info['display_id'] = lecture_slug if not multipart else '%s_part%s' % (lecture_slug, part_id)
                if multipart:
                    info['title'] += ' (Part %s)' % part_id
                switch = smil.find('.//switch')
                if switch is not None:
                    info['duration'] = parse_duration(switch.attrib.get('dur'))
                item_info = lecture_info.copy()
                item_info.update(info)
                return item_info

            if explicit_part_id or not multipart:
                result = extract_part(explicit_part_id or parts[0])
            else:
                result = {
                    '_type': 'multi_video',
                    'entries': [extract_part(part) for part in parts],
                }
                result.update(lecture_info)

            # Immediately return explicitly requested part or non event item
            if explicit_part_id or lecture_type != 'evt':
                return result

            playlist_entries.append(result)

        # It's probably a playlist
        if not parts or lecture_type == 'evt':
            playlist_webpage = self._download_webpage(
                '%s/site/ajax/drilldown/?id=%s' % (base_url, lecture_id), lecture_id)
            entries = [
                self.url_result(compat_urlparse.urljoin(url, video_url), 'Viidea')
                for _, video_url in re.findall(
                    r'<a[^>]+href=(["\'])(.+?)\1[^>]+id=["\']lec=\d+', playlist_webpage)]
            playlist_entries.extend(entries)

        playlist = self.playlist_result(playlist_entries, lecture_id)
        playlist.update(lecture_info)
        return playlist