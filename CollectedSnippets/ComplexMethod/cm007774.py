def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        article = self._parse_json(self._search_regex(
            r'window\.\$REACTBASE_STATE\.article(?:_multisite)?\s*=\s*({.+})',
            webpage, 'article'), display_id)['article']
        title = article.get('title')
        description = clean_html(article.get('leadParagraph')) or ''
        if article.get('editorialType') != 'VID':
            entries = []
            body = [article.get('opening')]
            body.extend(try_get(article, lambda x: x['body'], list) or [])
            for p in body:
                if not isinstance(p, dict):
                    continue
                content = p.get('content')
                if not content:
                    continue
                type_ = p.get('type')
                if type_ == 'paragraph':
                    content_str = str_or_none(content)
                    if content_str:
                        description += content_str
                    continue
                if type_ == 'video' and isinstance(content, dict):
                    entries.append(self._parse_content(content, url))
            return self.playlist_result(
                entries, str_or_none(article.get('id')), title, description)
        content = article['opening']['content']
        info = self._parse_content(content, url)
        info.update({
            'description': description,
        })
        return info