def _extract_embed_urls(cls, url, webpage):
        plyr_embeds = re.finditer(r'''(?x)
            <div[^>]+(?:
                data-plyr-embed-id="(?P<id1>[^"]+)"[^>]+data-plyr-provider="(?P<provider1>[^"]+)"|
                data-plyr-provider="(?P<provider2>[^"]+)"[^>]+data-plyr-embed-id="(?P<id2>[^"]+)"
            )[^>]*>''', webpage)
        for mobj in plyr_embeds:
            embed_id = mobj.group('id1') or mobj.group('id2')
            provider = mobj.group('provider1') or mobj.group('provider2')
            if provider == 'vimeo':
                if not re.match(r'https?://', embed_id):
                    embed_id = f'https://player.vimeo.com/video/{embed_id}'
                yield VimeoIE._smuggle_referrer(embed_id, url)
            elif provider == 'youtube':
                if not re.match(r'https?://', embed_id):
                    embed_id = f'https://youtube.com/watch?v={embed_id}'
                yield embed_id