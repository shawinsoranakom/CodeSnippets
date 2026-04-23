def test_subs_list_to_dict(self):
        assert traverse_obj([
            {'name': 'de', 'url': 'https://example.com/subs/de.vtt'},
            {'name': 'en', 'url': 'https://example.com/subs/en1.ass'},
            {'name': 'en', 'url': 'https://example.com/subs/en2.ass'},
        ], [..., {
            'id': 'name',
            'url': 'url',
        }, all, {subs_list_to_dict}]) == {
            'de': [{'url': 'https://example.com/subs/de.vtt'}],
            'en': [
                {'url': 'https://example.com/subs/en1.ass'},
                {'url': 'https://example.com/subs/en2.ass'},
            ],
        }, 'function should build subtitle dict from list of subtitles'
        assert traverse_obj([
            {'name': 'de', 'url': 'https://example.com/subs/de.ass'},
            {'name': 'de'},
            {'name': 'en', 'content': 'content'},
            {'url': 'https://example.com/subs/en'},
        ], [..., {
            'id': 'name',
            'data': 'content',
            'url': 'url',
        }, all, {subs_list_to_dict(lang=None)}]) == {
            'de': [{'url': 'https://example.com/subs/de.ass'}],
            'en': [{'data': 'content'}],
        }, 'subs with mandatory items missing should be filtered'
        assert traverse_obj([
            {'url': 'https://example.com/subs/de.ass', 'name': 'de'},
            {'url': 'https://example.com/subs/en', 'name': 'en'},
        ], [..., {
            'id': 'name',
            'ext': ['url', {determine_ext(default_ext=None)}],
            'url': 'url',
        }, all, {subs_list_to_dict(ext='ext')}]) == {
            'de': [{'url': 'https://example.com/subs/de.ass', 'ext': 'ass'}],
            'en': [{'url': 'https://example.com/subs/en', 'ext': 'ext'}],
        }, '`ext` should set default ext but leave existing value untouched'
        assert traverse_obj([
            {'name': 'en', 'url': 'https://example.com/subs/en2', 'prio': True},
            {'name': 'en', 'url': 'https://example.com/subs/en1', 'prio': False},
        ], [..., {
            'id': 'name',
            'quality': ['prio', {int}],
            'url': 'url',
        }, all, {subs_list_to_dict(ext='ext')}]) == {'en': [
            {'url': 'https://example.com/subs/en1', 'ext': 'ext'},
            {'url': 'https://example.com/subs/en2', 'ext': 'ext'},
        ]}, '`quality` key should sort subtitle list accordingly'
        assert traverse_obj([
            {'name': 'de', 'url': 'https://example.com/subs/de.ass'},
            {'name': 'de'},
            {'name': 'en', 'content': 'content'},
            {'url': 'https://example.com/subs/en'},
        ], [..., {
            'id': 'name',
            'url': 'url',
            'data': 'content',
        }, all, {subs_list_to_dict(lang='en')}]) == {
            'de': [{'url': 'https://example.com/subs/de.ass'}],
            'en': [
                {'data': 'content'},
                {'url': 'https://example.com/subs/en'},
            ],
        }, 'optionally provided lang should be used if no id available'
        assert traverse_obj([
            {'name': 1, 'url': 'https://example.com/subs/de1'},
            {'name': {}, 'url': 'https://example.com/subs/de2'},
            {'name': 'de', 'ext': 1, 'url': 'https://example.com/subs/de3'},
            {'name': 'de', 'ext': {}, 'url': 'https://example.com/subs/de4'},
        ], [..., {
            'id': 'name',
            'url': 'url',
            'ext': 'ext',
        }, all, {subs_list_to_dict(lang=None)}]) == {
            'de': [
                {'url': 'https://example.com/subs/de3'},
                {'url': 'https://example.com/subs/de4'},
            ],
        }, 'non str types should be ignored for id and ext'
        assert traverse_obj([
            {'name': 1, 'url': 'https://example.com/subs/de1'},
            {'name': {}, 'url': 'https://example.com/subs/de2'},
            {'name': 'de', 'ext': 1, 'url': 'https://example.com/subs/de3'},
            {'name': 'de', 'ext': {}, 'url': 'https://example.com/subs/de4'},
        ], [..., {
            'id': 'name',
            'url': 'url',
            'ext': 'ext',
        }, all, {subs_list_to_dict(lang='de')}]) == {
            'de': [
                {'url': 'https://example.com/subs/de1'},
                {'url': 'https://example.com/subs/de2'},
                {'url': 'https://example.com/subs/de3'},
                {'url': 'https://example.com/subs/de4'},
            ],
        }, 'non str types should be replaced by default id'