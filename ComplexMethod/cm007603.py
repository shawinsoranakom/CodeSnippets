def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        urls = []
        subtitles = {}
        for num, textstream in enumerate(smil.findall(self._xpath_ns('.//textstream', namespace))):
            src = textstream.get('src')
            if not src or src in urls:
                continue
            urls.append(src)
            ext = textstream.get('ext') or mimetype2ext(textstream.get('type')) or determine_ext(src)
            lang = textstream.get('systemLanguage') or textstream.get('systemLanguageName') or textstream.get('lang') or subtitles_lang
            subtitles.setdefault(lang, []).append({
                'url': src,
                'ext': ext,
            })
        return subtitles