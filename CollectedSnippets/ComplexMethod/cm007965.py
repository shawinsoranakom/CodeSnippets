def generate_report(
    all_updates: dict[str, tuple[str | None, str | None]],
) -> collections.abc.Iterator[str]:
    GITHUB_RE = re.compile(r'https://github\.com/(?P<owner>[0-9a-zA-Z_-]+)/(?P<repo>[0-9a-zA-Z_-]+)')

    yield 'package | old | new | diff | changelog'
    yield '--------|-----|-----|------|----------'
    for package, (old, new) in sorted(all_updates.items()):
        if package in WELLKNOWN_PACKAGES:
            github_info = WELLKNOWN_PACKAGES[package]
            changelog = ''

        else:
            project_urls = call_pypi_api(package)['info']['project_urls']
            github_info = next((
                mobj.groupdict() for url in project_urls.values()
                if (mobj := GITHUB_RE.match(url))), None)
            changelog = next((
                url for key, url in project_urls.items()
                if key.lower().startswith(('change', 'history', 'release '))), '')
            if changelog:
                name = urllib.parse.urlparse(changelog).path.rstrip('/').rpartition('/')[2] or 'changelog'
                changelog = f'[{name}](<{changelog}>)'

        md_old = old = old or ''
        md_new = new = new or ''
        if old and new:
            # bolden and italicize the differing parts
            old_parts = old.split('.')
            new_parts = new.split('.')

            offset = None
            for index, (old_part, new_part) in enumerate(zip(old_parts, new_parts, strict=False)):
                if old_part != new_part:
                    offset = index
                    break

            if offset is not None:
                md_old = '.'.join(old_parts[:offset]) + '.***' + '.'.join(old_parts[offset:]) + '***'
                md_new = '.'.join(new_parts[:offset]) + '.***' + '.'.join(new_parts[offset:]) + '***'

        compare = ''
        if github_info:
            tags_info = fetch_github_tags(
                github_info['owner'], github_info['repo'], fetch_tags=[old, new])
            old_tag = tags_info.get(old) and tags_info[old]['name']
            new_tag = tags_info.get(new) and tags_info[new]['name']
            github_url = 'https://github.com/{owner}/{repo}'.format(**github_info)
            if new_tag:
                md_new = f'[{md_new}]({github_url}/releases/tag/{new_tag})'
            if old_tag:
                md_old = f'[{md_old}]({github_url}/releases/tag/{old_tag})'
            if new_tag and old_tag:
                compare = f'[`{old_tag}...{new_tag}`]({github_url}/compare/{old_tag}...{new_tag})'

        yield ' | '.join((
            f'[**`{package}`**](https://pypi.org/project/{package})',
            md_old,
            md_new,
            compare,
            changelog,
        ))