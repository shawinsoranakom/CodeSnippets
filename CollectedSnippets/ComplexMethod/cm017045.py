def get_contributors(pr_nodes: list[PullRequestNode]) -> ContributorsResults:
    contributors = Counter[str]()
    translation_reviewers = Counter[str]()
    translators = Counter[str]()
    authors: dict[str, Author] = {}

    for pr in pr_nodes:
        if pr.author:
            authors[pr.author.login] = pr.author
        is_lang = False
        for label in pr.labels.nodes:
            if label.name == "lang-all":
                is_lang = True
                break
        for review in pr.reviews.nodes:
            if review.author:
                authors[review.author.login] = review.author
                if is_lang:
                    translation_reviewers[review.author.login] += 1
        if pr.state == "MERGED" and pr.author:
            if is_lang:
                translators[pr.author.login] += 1
            else:
                contributors[pr.author.login] += 1
    return ContributorsResults(
        contributors=contributors,
        translation_reviewers=translation_reviewers,
        translators=translators,
        authors=authors,
    )