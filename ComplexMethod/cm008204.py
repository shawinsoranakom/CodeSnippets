def _get_subtitles(self, *, ep_id=None, aid=None):
        sub_json = self._call_api(
            '/web/v2/subtitle', ep_id or aid, fatal=False,
            note='Downloading subtitles list', errnote='Unable to download subtitles list',
            query=filter_dict({
                'platform': 'web',
                's_locale': 'en_US',
                'episode_id': ep_id,
                'aid': aid,
            })) or {}
        subtitles = {}
        fetched_urls = set()
        for sub in traverse_obj(sub_json, (('subtitles', 'video_subtitle'), ..., {dict})):
            for url in traverse_obj(sub, ((None, 'ass', 'srt'), 'url', {url_or_none})):
                if url in fetched_urls:
                    continue
                fetched_urls.add(url)
                sub_ext = determine_ext(url)
                sub_lang = sub.get('lang_key') or 'en'

                if sub_ext == 'ass':
                    subtitles.setdefault(sub_lang, []).append({
                        'ext': 'ass',
                        'url': url,
                    })
                elif sub_ext == 'json':
                    sub_data = self._download_json(
                        url, ep_id or aid, fatal=False,
                        note=f'Downloading subtitles{format_field(sub, "lang", " for %s")} ({sub_lang})',
                        errnote='Unable to download subtitles')

                    if sub_data:
                        subtitles.setdefault(sub_lang, []).append({
                            'ext': 'srt',
                            'data': self.json2srt(sub_data),
                        })
                else:
                    self.report_warning('Unexpected subtitle extension', ep_id or aid)

        return subtitles