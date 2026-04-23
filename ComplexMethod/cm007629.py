def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        mv_data = {}
        if video_id:
            data = {
                'act': 'show_inline',
                'video': video_id,
            }
            # Some videos (removed?) can only be downloaded with list id specified
            list_id = mobj.group('list_id')
            if list_id:
                data['list'] = list_id

            payload = self._download_payload('al_video', video_id, data)
            info_page = payload[1]
            opts = payload[-1]
            mv_data = opts.get('mvData') or {}
            player = opts.get('player') or {}
        else:
            video_id = '%s_%s' % (mobj.group('oid'), mobj.group('id'))

            info_page = self._download_webpage(
                'http://vk.com/video_ext.php?' + mobj.group('embed_query'), video_id)

            error_message = self._html_search_regex(
                [r'(?s)<!><div[^>]+class="video_layer_message"[^>]*>(.+?)</div>',
                    r'(?s)<div[^>]+id="video_ext_msg"[^>]*>(.+?)</div>'],
                info_page, 'error message', default=None)
            if error_message:
                raise ExtractorError(error_message, expected=True)

            if re.search(r'<!>/login\.php\?.*\bact=security_check', info_page):
                raise ExtractorError(
                    'You are trying to log in from an unusual location. You should confirm ownership at vk.com to log in with this IP.',
                    expected=True)

            ERROR_COPYRIGHT = 'Video %s has been removed from public access due to rightholder complaint.'

            ERRORS = {
                r'>Видеозапись .*? была изъята из публичного доступа в связи с обращением правообладателя.<':
                ERROR_COPYRIGHT,

                r'>The video .*? was removed from public access by request of the copyright holder.<':
                ERROR_COPYRIGHT,

                r'<!>Please log in or <':
                'Video %s is only available for registered users, '
                'use --username and --password options to provide account credentials.',

                r'<!>Unknown error':
                'Video %s does not exist.',

                r'<!>Видео временно недоступно':
                'Video %s is temporarily unavailable.',

                r'<!>Access denied':
                'Access denied to video %s.',

                r'<!>Видеозапись недоступна, так как её автор был заблокирован.':
                'Video %s is no longer available, because its author has been blocked.',

                r'<!>This video is no longer available, because its author has been blocked.':
                'Video %s is no longer available, because its author has been blocked.',

                r'<!>This video is no longer available, because it has been deleted.':
                'Video %s is no longer available, because it has been deleted.',

                r'<!>The video .+? is not available in your region.':
                'Video %s is not available in your region.',
            }

            for error_re, error_msg in ERRORS.items():
                if re.search(error_re, info_page):
                    raise ExtractorError(error_msg % video_id, expected=True)

            player = self._parse_json(self._search_regex(
                r'var\s+playerParams\s*=\s*({.+?})\s*;\s*\n',
                info_page, 'player params'), video_id)

        youtube_url = YoutubeIE._extract_url(info_page)
        if youtube_url:
            return self.url_result(youtube_url, YoutubeIE.ie_key())

        vimeo_url = VimeoIE._extract_url(url, info_page)
        if vimeo_url is not None:
            return self.url_result(vimeo_url, VimeoIE.ie_key())

        pladform_url = PladformIE._extract_url(info_page)
        if pladform_url:
            return self.url_result(pladform_url, PladformIE.ie_key())

        m_rutube = re.search(
            r'\ssrc="((?:https?:)?//rutube\.ru\\?/(?:video|play)\\?/embed(?:.*?))\\?"', info_page)
        if m_rutube is not None:
            rutube_url = self._proto_relative_url(
                m_rutube.group(1).replace('\\', ''))
            return self.url_result(rutube_url)

        dailymotion_urls = DailymotionIE._extract_urls(info_page)
        if dailymotion_urls:
            return self.url_result(dailymotion_urls[0], DailymotionIE.ie_key())

        odnoklassniki_url = OdnoklassnikiIE._extract_url(info_page)
        if odnoklassniki_url:
            return self.url_result(odnoklassniki_url, OdnoklassnikiIE.ie_key())

        sibnet_urls = self._extract_sibnet_urls(info_page)
        if sibnet_urls:
            return self.url_result(sibnet_urls[0])

        m_opts = re.search(r'(?s)var\s+opts\s*=\s*({.+?});', info_page)
        if m_opts:
            m_opts_url = re.search(r"url\s*:\s*'((?!/\b)[^']+)", m_opts.group(1))
            if m_opts_url:
                opts_url = m_opts_url.group(1)
                if opts_url.startswith('//'):
                    opts_url = 'http:' + opts_url
                return self.url_result(opts_url)

        data = player['params'][0]
        title = unescapeHTML(data['md_title'])

        # 2 = live
        # 3 = post live (finished live)
        is_live = data.get('live') == 2
        if is_live:
            title = self._live_title(title)

        timestamp = unified_timestamp(self._html_search_regex(
            r'class=["\']mv_info_date[^>]+>([^<]+)(?:<|from)', info_page,
            'upload date', default=None)) or int_or_none(data.get('date'))

        view_count = str_to_int(self._search_regex(
            r'class=["\']mv_views_count[^>]+>\s*([\d,.]+)',
            info_page, 'view count', default=None))

        formats = []
        for format_id, format_url in data.items():
            format_url = url_or_none(format_url)
            if not format_url or not format_url.startswith(('http', '//', 'rtmp')):
                continue
            if (format_id.startswith(('url', 'cache'))
                    or format_id in ('extra_data', 'live_mp4', 'postlive_mp4')):
                height = int_or_none(self._search_regex(
                    r'^(?:url|cache)(\d+)', format_id, 'height', default=None))
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'height': height,
                })
            elif format_id == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False, live=is_live))
            elif format_id == 'rtmp':
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'ext': 'flv',
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': data.get('jpg'),
            'uploader': data.get('md_author'),
            'uploader_id': str_or_none(data.get('author_id') or mv_data.get('authorId')),
            'duration': int_or_none(data.get('duration') or mv_data.get('duration')),
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': int_or_none(mv_data.get('likes')),
            'comment_count': int_or_none(mv_data.get('commcount')),
            'is_live': is_live,
        }