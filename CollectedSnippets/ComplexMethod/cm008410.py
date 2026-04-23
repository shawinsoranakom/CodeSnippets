def _entries(self, url, page, category_id):
        content = page
        is_billennium_tabs = 'onclick="TB_LoadTab(' in page
        is_post_back = 'onclick="__doPostBack(' in page
        pagination = page if is_billennium_tabs else None
        for page_num in itertools.count(2):
            for a_entry, entry_id in re.findall(
                    r'(?s)<article[^>]+>.*?(<a[^>]+href=["\'](?:(?:https?)?://[^/]+)?/\d+/\d+/Artykul/(\d+)[^>]+>).*?</article>',
                    content):
                entry = extract_attributes(a_entry)
                if entry.get('href'):
                    yield self.url_result(
                        urljoin(url, entry['href']), PolskieRadioLegacyIE, entry_id, entry.get('title'))
            for a_entry in re.findall(r'<span data-media=({[^ ]+})', content):
                yield traverse_obj(self._parse_json(a_entry, category_id), {
                    'url': 'file',
                    'id': 'uid',
                    'duration': 'length',
                    'title': ('title', {urllib.parse.unquote}),
                    'description': ('desc', {urllib.parse.unquote}),
                })
            if is_billennium_tabs:
                params = self._search_json(
                    r'<div[^>]+class=["\']next["\'][^>]*>\s*<a[^>]+onclick=["\']TB_LoadTab\(',
                    pagination, 'next page params', category_id, default=None, close_objects=1,
                    contains_pattern='.+', transform_source=lambda x: f'[{js_to_json(unescapeHTML(x))}')
                if not params:
                    break
                tab_content = self._download_json(
                    'https://www.polskieradio.pl/CMS/TemplateBoxesManagement/TemplateBoxTabContent.aspx/GetTabContent',
                    category_id, f'Downloading page {page_num}', headers={'content-type': 'application/json'},
                    data=json.dumps(dict(zip((  # noqa: B905
                        'boxInstanceId', 'tabId', 'categoryType', 'sectionId', 'categoryId', 'pagerMode',
                        'subjectIds', 'tagIndexId', 'queryString', 'name', 'openArticlesInParentTemplate',
                        'idSectionFromUrl', 'maxDocumentAge', 'showCategoryForArticle', 'pageNumber',
                    ), params))).encode())['d']
                content, pagination = tab_content['Content'], tab_content.get('PagerContent')
            elif is_post_back:
                target = self._search_regex(
                    r'onclick=(?:["\'])__doPostBack\((?P<q1>["\'])(?P<target>[\w$]+)(?P=q1)\s*,\s*(?P<q2>["\'])Next(?P=q2)',
                    content, 'pagination postback target', group='target', default=None)
                if not target:
                    break
                content = self._download_webpage(
                    url, category_id, f'Downloading page {page_num}',
                    data=urllib.parse.urlencode({
                        **self._hidden_inputs(content),
                        '__EVENTTARGET': target,
                        '__EVENTARGUMENT': 'Next',
                    }).encode())
            else:
                next_url = urljoin(url, self._search_regex(
                    r'<div[^>]+class=["\']next["\'][^>]*>\s*<a[^>]+href=(["\'])(?P<url>(?:(?!\1).)+)\1',
                    content, 'next page url', group='url', default=None))
                if not next_url:
                    break
                content = self._download_webpage(next_url, category_id, f'Downloading page {page_num}')