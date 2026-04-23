def process_subtitles(vod_data, process_url):
        ret = {'subtitles': {}, 'automatic_captions': {}}
        for caption in traverse_obj(vod_data, ('captions', 'list', ...)):
            caption_url = caption.get('source')
            if not caption_url:
                continue
            type_ = 'automatic_captions' if caption.get('type') == 'auto' else 'subtitles'
            lang = caption.get('locale') or join_nonempty('language', 'country', from_dict=caption) or 'und'
            if caption.get('type') == 'fan':
                lang += '_fan{}'.format(next(i for i in itertools.count(1) if f'{lang}_fan{i}' not in ret[type_]))
            ret[type_].setdefault(lang, []).extend({
                'url': sub_url,
                'name': join_nonempty('label', 'fanName', from_dict=caption, delim=' - '),
            } for sub_url in process_url(caption_url))
        return ret