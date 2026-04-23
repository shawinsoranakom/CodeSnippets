def _real_extract(self, url):
        post_id = self._match_id(url)

        post = self._call_api(
            'post/v1.0/post-%s', post_id,
            'attachments{video},officialVideo{videoSeq},plainBody,title')

        video_seq = str_or_none(try_get(
            post, lambda x: x['officialVideo']['videoSeq']))
        if video_seq:
            return self.url_result(
                'http://www.vlive.tv/video/' + video_seq,
                VLiveIE.ie_key(), video_seq)

        title = post['title']
        entries = []
        for idx, video in enumerate(post['attachments']['video'].values()):
            video_id = video.get('videoId')
            if not video_id:
                continue
            upload_type = video.get('uploadType')
            upload_info = video.get('uploadInfo') or {}
            entry = None
            if upload_type == 'SOS':
                download = self._call_api(
                    self._SOS_TMPL, video_id)['videoUrl']['download']
                formats = []
                for f_id, f_url in download.items():
                    formats.append({
                        'format_id': f_id,
                        'url': f_url,
                        'height': int_or_none(f_id[:-1]),
                    })
                self._sort_formats(formats)
                entry = {
                    'formats': formats,
                    'id': video_id,
                    'thumbnail': upload_info.get('imageUrl'),
                }
            elif upload_type == 'V':
                vod_id = upload_info.get('videoId')
                if not vod_id:
                    continue
                inkey = self._call_api(self._INKEY_TMPL, video_id)['inKey']
                entry = self._extract_video_info(video_id, vod_id, inkey)
            if entry:
                entry['title'] = '%s_part%s' % (title, idx)
                entries.append(entry)
        return self.playlist_result(
            entries, post_id, title, strip_or_none(post.get('plainBody')))