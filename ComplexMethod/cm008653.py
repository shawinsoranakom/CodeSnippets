def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        nt = mobj.group('nt') or mobj.group('nt_de')
        lecture_id = mobj.group('id')
        display_id = nt or lecture_id
        api_path = 'lectures/' + lecture_id if lecture_id else 'lecture/' + nt + '.json'
        video = self._download_json(
            self._API_BASE_URL + api_path, display_id)
        title = video['title'].strip()
        if not lecture_id:
            pid = video.get('productId') or video.get('uid')
            if pid:
                spid = pid.split('_')
                if spid and len(spid) == 2:
                    lecture_id = spid[1]

        formats = []
        for format_ in video['content']['media']:
            if not isinstance(format_, dict):
                continue
            file_ = format_.get('file')
            if not file_:
                continue
            ext = determine_ext(file_)
            if ext == 'smil':
                # smil contains only broken RTMP formats anyway
                continue
            file_url = url_or_none(file_)
            if not file_url:
                continue
            label = str_or_none(format_.get('label'))
            filesize = int_or_none(format_.get('fileSize'))
            f = {
                'url': file_url,
                'format_id': label,
                'filesize': float_or_none(filesize, invscale=1000),
            }
            if label:
                mobj = re.match(r'(\d+)p\s*\(([^)]+)\)', label)
                if mobj:
                    f.update({
                        'format_id': mobj.group(2),
                        'height': int(mobj.group(1)),
                    })
            formats.append(f)

        subtitles = {}
        automatic_captions = {}
        captions = video.get('captions') or []
        for cc in captions:
            cc_url = cc.get('url')
            if not cc_url:
                continue
            cc_label = cc.get('translatedCode')
            lang = cc.get('languageCode') or self._search_regex(
                r'/([a-z]{2})_', cc_url, 'lang',
                default=cc_label.split()[0] if cc_label else 'en')
            original_lang = self._search_regex(
                r'/[a-z]{2}_([a-z]{2})_', cc_url, 'original lang',
                default=None)
            sub_dict = (automatic_captions
                        if 'auto-translated' in cc_label or original_lang
                        else subtitles)
            sub_dict.setdefault(self._CC_LANGS.get(lang, lang), []).append({
                'url': cc_url,
            })

        return {
            'id': lecture_id or nt,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'automatic_captions': automatic_captions,
        }