def expect_info_dict(self, got_dict, expected_dict):
    expect_dict(self, got_dict, expected_dict)
    # Check for the presence of mandatory fields
    if got_dict.get('_type') not in ('playlist', 'multi_video'):
        for key in ('id', 'url', 'title', 'ext'):
            self.assertTrue(got_dict.get(key), 'Missing mandatory field %s' % key)
    # Check for mandatory fields that are automatically set by YoutubeDL
    for key in ['webpage_url', 'extractor', 'extractor_key']:
        self.assertTrue(got_dict.get(key), 'Missing field: %s' % key)

    # Are checkable fields missing from the test case definition?
    test_info_dict = dict((key, value if not isinstance(value, compat_str) or len(value) < 250 else 'md5:' + md5(value))
                          for key, value in got_dict.items()
                          if value and key in ('id', 'title', 'description', 'uploader', 'upload_date', 'timestamp', 'uploader_id', 'location', 'age_limit'))
    missing_keys = set(test_info_dict.keys()) - set(expected_dict.keys())
    if missing_keys:
        def _repr(v):
            if isinstance(v, compat_str):
                return "'%s'" % v.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
            else:
                return repr(v)
        info_dict_str = ''
        if len(missing_keys) != len(expected_dict):
            info_dict_str += ''.join(
                '    %s: %s,\n' % (_repr(k), _repr(v))
                for k, v in test_info_dict.items() if k not in missing_keys)

            if info_dict_str:
                info_dict_str += '\n'
        info_dict_str += ''.join(
            '    %s: %s,\n' % (_repr(k), _repr(test_info_dict[k]))
            for k in missing_keys)
        write_string(
            '\n\'info_dict\': {\n' + info_dict_str + '},\n', out=sys.stderr)
        self.assertFalse(
            missing_keys,
            'Missing keys in test definition: %s' % (
                ', '.join(sorted(missing_keys))))