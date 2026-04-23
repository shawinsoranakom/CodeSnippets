def _extract_brightcove_urls(ie, webpage):
        # Reference:
        # 1. http://docs.brightcove.com/en/video-cloud/brightcove-player/guides/publish-video.html#setvideoiniframe
        # 2. http://docs.brightcove.com/en/video-cloud/brightcove-player/guides/publish-video.html#tag
        # 3. http://docs.brightcove.com/en/video-cloud/brightcove-player/guides/publish-video.html#setvideousingjavascript
        # 4. http://docs.brightcove.com/en/video-cloud/brightcove-player/guides/in-page-embed-player-implementation.html
        # 5. https://support.brightcove.com/en/video-cloud/docs/dynamically-assigning-videos-player

        entries = []

        # Look for iframe embeds [1]
        for _, url in re.findall(
                r'<iframe[^>]+src=(["\'])((?:https?:)?//players\.brightcove\.net/\d+/[^/]+/index\.html.+?)\1', webpage):
            entries.append(url if url.startswith(('http:', 'https:')) else 'https:' + url)

        # Look for <video> tags [2] and embed_in_page embeds [3]
        # [2] looks like:
        for video, script_tag, account_id, player_id, embed in re.findall(
                r'''(?isx)
                    (<video(?:-js)?\s+[^>]*\bdata-video-id\s*=\s*['"]?[^>]+>)
                    (?:.*?
                        (<script[^>]+
                            src=["\'](?:https?:)?//players\.brightcove\.net/
                            (\d+)/([^/]+)_([^/]+)/index(?:\.min)?\.js
                        )
                    )?
                ''', webpage):
            attrs = extract_attributes(video)

            # According to examples from [4] it's unclear whether video id
            # may be optional and what to do when it is
            video_id = attrs.get('data-video-id')
            if not video_id:
                continue

            account_id = account_id or attrs.get('data-account')
            if not account_id:
                continue

            player_id = player_id or attrs.get('data-player') or 'default'
            embed = embed or attrs.get('data-embed') or 'default'

            bc_url = f'https://players.brightcove.net/{account_id}/{player_id}_{embed}/index.html?videoId={video_id}'

            # Some brightcove videos may be embedded with video tag only and
            # without script tag or any mentioning of brightcove at all. Such
            # embeds are considered ambiguous since they are matched based only
            # on data-video-id and data-account attributes and in the wild may
            # not be brightcove embeds at all. Let's check reconstructed
            # brightcove URLs in case of such embeds and only process valid
            # ones. By this we ensure there is indeed a brightcove embed.
            if not script_tag and not ie._is_valid_url(
                    bc_url, video_id, 'possible brightcove video'):
                continue

            entries.append(bc_url)

        return entries