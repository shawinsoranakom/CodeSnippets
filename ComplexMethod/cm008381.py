def _remove_duplicate_formats(formats):
        seen_urls = set()
        seen_fragment_urls = set()
        unique_formats = []
        for f in formats:
            fragments = f.get('fragments')
            if callable(fragments):
                unique_formats.append(f)

            elif fragments:
                fragment_urls = frozenset(
                    fragment.get('url') or urljoin(f['fragment_base_url'], fragment['path'])
                    for fragment in fragments)
                if fragment_urls not in seen_fragment_urls:
                    seen_fragment_urls.add(fragment_urls)
                    unique_formats.append(f)

            elif f['url'] not in seen_urls:
                seen_urls.add(f['url'])
                unique_formats.append(f)

        formats[:] = unique_formats