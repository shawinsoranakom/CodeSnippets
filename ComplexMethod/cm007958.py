def fetch_github_tags(
    owner: str,
    repo: str,
    *,
    fetch_tags: list[str] | None = None,
) -> dict[str, dict[str, typing.Any]]:

    needed_tags = set(fetch_tags or [])
    results = {}

    for page in itertools.count(1):
        print(f'Fetching tags list page {page} from Github API: {owner}/{repo}', file=sys.stderr)
        tags = call_github_api(
            f'/repos/{owner}/{repo}/tags',
            query={'per_page': '100', 'page': page})

        if not tags:
            break

        if not fetch_tags:
            # Fetch all tags
            results.update({tag['name']: tag for tag in tags})
            continue

        for tag in tags:
            clean_tag = tag['name'].removeprefix('v')
            possible_matches = {tag['name'], clean_tag}
            # Normalize calver tags like 2024.01.01 to 2024.1.1
            with contextlib.suppress(ValueError):
                possible_matches.add('.'.join(map(str, map(int, clean_tag.split('.')))))

            for name in possible_matches:
                if name in needed_tags:
                    needed_tags.remove(name)
                    results[name] = tag
                    break  # from inner loop

            if not needed_tags:
                break

        if not needed_tags:
            break

    return results