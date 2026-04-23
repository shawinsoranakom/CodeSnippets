def sanitize_got_info_dict(got_dict):
    IGNORED_FIELDS = (
        *YoutubeDL._format_fields,

        # Lists
        'formats', 'thumbnails', 'subtitles', 'automatic_captions', 'comments', 'entries',

        # Auto-generated
        'autonumber', 'playlist', 'format_index', 'video_ext', 'audio_ext', 'duration_string', 'epoch', 'n_entries',
        'fulltitle', 'extractor', 'extractor_key', 'filename', 'filepath', 'infojson_filename', 'original_url',

        # Only live_status needs to be checked
        'is_live', 'was_live',
    )

    IGNORED_PREFIXES = ('', 'playlist', 'requested', 'webpage')

    def sanitize(key, value):
        if isinstance(value, str) and len(value) > 100 and key != 'thumbnail':
            return f'md5:{md5(value)}'
        elif isinstance(value, list) and len(value) > 10:
            return f'count:{len(value)}'
        elif key.endswith('_count') and isinstance(value, int):
            return int
        return value

    test_info_dict = {
        key: sanitize(key, value) for key, value in got_dict.items()
        if value is not None and key not in IGNORED_FIELDS and (
            not any(key.startswith(f'{prefix}_') for prefix in IGNORED_PREFIXES)
            or key == '_old_archive_ids')
    }

    # display_id may be generated from id
    if test_info_dict.get('display_id') == test_info_dict.get('id'):
        test_info_dict.pop('display_id')

    # Remove deprecated fields
    for old in YoutubeDL._deprecated_multivalue_fields:
        test_info_dict.pop(old, None)

    # release_year may be generated from release_date
    if try_call(lambda: test_info_dict['release_year'] == int(test_info_dict['release_date'][:4])):
        test_info_dict.pop('release_year')

    # Check url for flat entries
    if got_dict.get('_type', 'video') != 'video' and got_dict.get('url'):
        test_info_dict['url'] = got_dict['url']

    return test_info_dict