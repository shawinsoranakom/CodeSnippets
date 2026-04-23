def _parse_video_config(self, video_config, display_id):
        video_config = self._parse_json(video_config, display_id)
        item = video_config['playlist'][0]
        mcp_id = item.get('mcpID')
        if mcp_id:
            info = self.url_result(
                'anvato:GXvEgwyJeWem8KCYXfeoHWknwP48Mboj:' + mcp_id,
                'Anvato', mcp_id)
        else:
            media_id = item.get('id') or item['entityId']
            title = item['title']
            item_url = item['url']
            info = {'id': media_id}
            ext = determine_ext(item_url)
            if ext == 'm3u8':
                info['formats'] = self._extract_m3u8_formats(item_url, media_id, 'mp4')
                self._sort_formats(info['formats'])
            else:
                info['url'] = item_url
                if item.get('audio') is True:
                    info['vcodec'] = 'none'
            is_live = video_config.get('live') is True
            thumbnails = None
            image_url = item.get(item.get('imageSrc')) or item.get(item.get('posterImage'))
            if image_url:
                thumbnails = [{
                    'url': image_url,
                    'ext': determine_ext(image_url, 'jpg'),
                }]
            info.update({
                'title': self._live_title(title) if is_live else title,
                'is_live': is_live,
                'description': clean_html(item.get('description')),
                'thumbnails': thumbnails,
            })
        return info