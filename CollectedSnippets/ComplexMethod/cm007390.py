def _extract_entry(self, url, player, content, video_id):
        title = content.get('title') or content['teaserHeadline']

        t = content['mainVideoContent']['http://zdf.de/rels/target']

        def get_ptmd_path(d):
            return (
                d.get('http://zdf.de/rels/streams/ptmd')
                or d.get('http://zdf.de/rels/streams/ptmd-template',
                         '').replace('{playerId}', 'ngplayer_2_4'))

        ptmd_path = get_ptmd_path(try_get(t, lambda x: x['streams']['default'], dict) or {})
        if not ptmd_path:
            ptmd_path = get_ptmd_path(t)

        if not ptmd_path:
            raise ExtractorError('Could not extract ptmd_path')

        info = self._extract_ptmd(
            urljoin(url, ptmd_path), video_id, player['apiToken'], url)

        thumbnails = []
        layouts = try_get(
            content, lambda x: x['teaserImageRef']['layouts'], dict)
        if layouts:
            for layout_key, layout_url in layouts.items():
                layout_url = url_or_none(layout_url)
                if not layout_url:
                    continue
                thumbnail = {
                    'url': layout_url,
                    'format_id': layout_key,
                }
                mobj = re.search(r'(?P<width>\d+)x(?P<height>\d+)', layout_key)
                if mobj:
                    thumbnail.update({
                        'width': int(mobj.group('width')),
                        'height': int(mobj.group('height')),
                    })
                thumbnails.append(thumbnail)

        return merge_dicts(info, {
            'title': title,
            'description': content.get('leadParagraph') or content.get('teasertext'),
            'duration': int_or_none(t.get('duration')),
            'timestamp': unified_timestamp(content.get('editorialDate')),
            'thumbnails': thumbnails,
        })