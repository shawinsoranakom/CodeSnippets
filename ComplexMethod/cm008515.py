def _extract_song(song_data, url=None):
        info = traverse_obj(song_data, {
            'id': ('id', {str}),
            'title': (('song', 'title'), {clean_html}, any),
            'album': ((None, 'more_info'), 'album', {clean_html}, any),
            'duration': ((None, 'more_info'), 'duration', {int_or_none}, any),
            'channel': ((None, 'more_info'), 'label', {str}, any),
            'channel_id': ((None, 'more_info'), 'label_id', {str}, any),
            'channel_url': ((None, 'more_info'), 'label_url', {urljoin('https://www.jiosaavn.com/')}, any),
            'release_date': ((None, 'more_info'), 'release_date', {unified_strdate}, any),
            'release_year': ('year', {int_or_none}),
            'thumbnail': ('image', {url_or_none}, {lambda x: re.sub(r'-\d+x\d+\.', '-500x500.', x)}),
            'view_count': ('play_count', {int_or_none}),
            'language': ('language', {lambda x: ISO639Utils.short2long(x.casefold()) or 'und'}),
            'webpage_url': ('perma_url', {url_or_none}),
            'artists': ('more_info', 'artistMap', 'primary_artists', ..., 'name', {str}, filter, all),
        })
        if webpage_url := info.get('webpage_url') or url:
            info['display_id'] = url_basename(webpage_url)
            info['_old_archive_ids'] = [make_archive_id(JioSaavnSongIE, info['display_id'])]

        if primary_artists := traverse_obj(song_data, ('primary_artists', {lambda x: x.split(', ') if x else None})):
            info['artists'].extend(primary_artists)
        if featured_artists := traverse_obj(song_data, ('featured_artists', {str}, filter)):
            info['artists'].extend(featured_artists.split(', '))
        info['artists'] = orderedSet(info['artists']) or None

        return info