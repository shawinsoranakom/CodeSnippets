def expect_info_dict(self, got_dict, expected_dict):
    ALLOWED_KEYS_SORT_ORDER = (
        # NB: Keep in sync with the docstring of extractor/common.py
        'ie_key', 'url', 'id', 'ext', 'direct', 'display_id', 'title', 'alt_title', 'description', 'media_type',
        'uploader', 'uploader_id', 'uploader_url', 'channel', 'channel_id', 'channel_url', 'channel_is_verified',
        'channel_follower_count', 'comment_count', 'view_count', 'concurrent_view_count', 'save_count',
        'like_count', 'dislike_count', 'repost_count', 'average_rating', 'age_limit', 'duration', 'thumbnail', 'heatmap',
        'chapters', 'chapter', 'chapter_number', 'chapter_id', 'start_time', 'end_time', 'section_start', 'section_end',
        'categories', 'tags', 'cast', 'composers', 'artists', 'album_artists', 'creators', 'genres',
        'track', 'track_number', 'track_id', 'album', 'album_type', 'disc_number',
        'series', 'series_id', 'season', 'season_number', 'season_id', 'episode', 'episode_number', 'episode_id',
        'timestamp', 'upload_date', 'release_timestamp', 'release_date', 'release_year', 'modified_timestamp', 'modified_date',
        'playable_in_embed', 'availability', 'live_status', 'location', 'license', '_old_archive_ids',
    )

    expect_dict(self, got_dict, expected_dict)
    # Check for the presence of mandatory fields
    if got_dict.get('_type') not in ('playlist', 'multi_video'):
        mandatory_fields = ['id', 'title']
        if expected_dict.get('ext'):
            mandatory_fields.extend(('url', 'ext'))
        for key in mandatory_fields:
            self.assertTrue(got_dict.get(key), f'Missing mandatory field {key}')
    # Check for mandatory fields that are automatically set by YoutubeDL
    if got_dict.get('_type', 'video') == 'video':
        for key in ['webpage_url', 'extractor', 'extractor_key']:
            self.assertTrue(got_dict.get(key), f'Missing field: {key}')

    test_info_dict = sanitize_got_info_dict(got_dict)

    # Check for invalid/misspelled field names being returned by the extractor
    invalid_keys = sorted(test_info_dict.keys() - ALLOWED_KEYS_SORT_ORDER)
    self.assertFalse(invalid_keys, f'Invalid fields returned by the extractor: {", ".join(invalid_keys)}')

    missing_keys = sorted(
        test_info_dict.keys() - expected_dict.keys(),
        key=ALLOWED_KEYS_SORT_ORDER.index)
    if missing_keys:
        def _repr(v):
            if isinstance(v, str):
                return "'{}'".format(v.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n'))
            elif isinstance(v, type):
                return v.__name__
            else:
                return repr(v)
        info_dict_str = ''.join(
            f'    {_repr(k)}: {_repr(v)},\n'
            for k, v in test_info_dict.items() if k not in missing_keys)
        if info_dict_str:
            info_dict_str += '\n'
        info_dict_str += ''.join(
            f'    {_repr(k)}: {_repr(test_info_dict[k])},\n'
            for k in missing_keys)
        info_dict_str = '\n\'info_dict\': {\n' + info_dict_str + '},\n'
        write_string(info_dict_str.replace('\n', '\n        '), out=sys.stderr)
        self.assertFalse(
            missing_keys,
            'Missing keys in test definition: {}'.format(', '.join(sorted(missing_keys))))