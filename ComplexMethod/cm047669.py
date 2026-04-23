def extract_spreadsheet_terms(fileobj, keywords, comment_tags, options):
    """Babel message extractor for spreadsheet data files.

    :param fileobj: the file-like object the messages should be extracted from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    """
    terms = set()
    data = json.load(fileobj)
    for sheet in data.get('sheets', []):
        for cell in sheet['cells'].values():
            # 'cell' was an object in versions <saas-18.1
            content = cell if isinstance(cell, str) else cell.get('content', '')
            if content.startswith('='):
                terms.update(extract_formula_terms(content))
            else:
                markdown_link = re.fullmatch(r'\[(.+)\]\(.+\)', content)
                if markdown_link:
                    terms.add(markdown_link[1])
        for figure in sheet['figures']:
            if figure['tag'] == 'chart':
                title = figure['data']['title']
                if isinstance(title, str):
                    terms.add(title)
                elif 'text' in title:
                    terms.add(title['text'])
                if 'axesDesign' in figure['data']:
                    terms.update(
                        axes.get('title', {}).get('text', '') for axes in figure['data']['axesDesign'].values()
                    )
                if 'text' in (baselineDescr := figure['data'].get('baselineDescr', {})):
                    terms.add(baselineDescr['text'])
                if 'text' in (keyDescr := figure['data'].get('keyDescr', {})):
                    terms.add(keyDescr['text'])
    terms.update(global_filter['label'] for global_filter in data.get('globalFilters', []))
    return (
        (0, None, term, [])
        for term in terms
        if any(x.isalpha() for x in term)
    )