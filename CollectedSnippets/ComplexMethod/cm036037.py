def collect(path: Path):
    if path.is_file():
        html = path.relative_to(HOME)
        if html.suffix not in {'.py'}:
            return []

        if html.stem == '__init__':
            html = html.parent / 'index.html'
        else:
            html = html.parent / f'{html.stem}.html'

        if str(html) in IGNORE:
            return []

        with open(str(path), 'r') as f:
            contents = f.read()
            papers = set()
            for m in REGEX.finditer(contents):
                if m.group('id') in IGNORE_PAPERS:
                    continue
                papers.add(m.group('id'))

            if len(papers) > 1:
                logger.log([(str(html), Text.key), ': ', str(papers)])
            return [{'url': str(html), 'arxiv_id': p} for p in papers]

    urls = []
    for f in path.iterdir():
        urls += collect(f)

    return urls