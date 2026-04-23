def process_subtitles(self, video_id, normal_subtitles, automatic_captions):
        """Select the requested subtitles and their format"""
        available_subs = {}
        if normal_subtitles and self.params.get('writesubtitles'):
            available_subs.update(normal_subtitles)
        if automatic_captions and self.params.get('writeautomaticsub'):
            for lang, cap_info in automatic_captions.items():
                if lang not in available_subs:
                    available_subs[lang] = cap_info

        if (not self.params.get('writesubtitles') and not
                self.params.get('writeautomaticsub') or not
                available_subs):
            return None

        if self.params.get('allsubtitles', False):
            requested_langs = available_subs.keys()
        else:
            if self.params.get('subtitleslangs', False):
                requested_langs = self.params.get('subtitleslangs')
            elif 'en' in available_subs:
                requested_langs = ['en']
            else:
                requested_langs = [list(available_subs.keys())[0]]

        formats_query = self.params.get('subtitlesformat', 'best')
        formats_preference = formats_query.split('/') if formats_query else []
        subs = {}
        for lang in requested_langs:
            formats = available_subs.get(lang)
            if formats is None:
                self.report_warning('%s subtitles not available for %s' % (lang, video_id))
                continue
            for ext in formats_preference:
                if ext == 'best':
                    f = formats[-1]
                    break
                matches = list(filter(lambda f: f['ext'] == ext, formats))
                if matches:
                    f = matches[-1]
                    break
            else:
                f = formats[-1]
                self.report_warning(
                    'No subtitle format found matching "%s" for language %s, '
                    'using %s' % (formats_query, lang, f['ext']))
            subs[lang] = f
        return subs