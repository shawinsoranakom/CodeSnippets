def version_github_linkcode_resolve(domain, info):
    return github_links.github_linkcode_resolve(
        domain, info, version=version, next_version=django_next_version
    )