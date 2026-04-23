def search_backport(pr, g, ansible_ansible):
    """
    Do magic. This is basically the "brain" of 'auto'.
    It will search the PR (the newest PR - the backport) and try to find where
    it originated.

    First it will search in the title. Some titles include things like
    "foo bar change (#12345)" or "foo bar change (backport of #54321)"
    so we search for those and pull them out.

    Next it will scan the body of the PR and look for:
      - cherry-pick reference lines (e.g. "cherry-picked from commit XXXXX")
      - other PRs (#nnnnnn) and (foo/bar#nnnnnnn)
      - full URLs to other PRs

    It will take all of the above, and return a list of "possibilities",
    which is a list of PullRequest objects.
    """

    possibilities = []

    # 1. Try searching for it in the title.
    title_search = PULL_BACKPORT_IN_TITLE.match(pr.title)
    if title_search:
        ticket = title_search.group('ticket1')
        if not ticket:
            ticket = title_search.group('ticket2')
        try:
            possibilities.append(ansible_ansible.get_pull(int(ticket)))
        except Exception:
            pass

    # 2. Search for clues in the body of the PR
    body_lines = pr.body.split('\n')
    for line in body_lines:
        # a. Try searching for a `git cherry-pick` line
        cherrypick = PULL_CHERRY_PICKED_FROM.match(line)
        if cherrypick:
            prs = get_prs_for_commit(g, cherrypick.group('hash'))
            possibilities.extend(prs)
            continue

        # b. Try searching for other referenced PRs (by #nnnnn or full URL)
        tickets = [('ansible', 'ansible', ticket) for ticket in TICKET_NUMBER.findall(line)]
        tickets.extend(PULL_HTTP_URL_RE.findall(line))
        tickets.extend(PULL_URL_RE.findall(line))
        if tickets:
            for ticket in tickets:
                # Is it a PR (even if not in ansible/ansible)?
                # TODO: As a small optimization/to avoid extra calls to GitHub,
                # we could limit this check to non-URL matches. If it's a URL,
                # we know it's definitely a pull request.
                try:
                    repo_path = '{0}/{1}'.format(ticket[0], ticket[1])
                    repo = ansible_ansible
                    if repo_path != 'ansible/ansible':
                        repo = g.get_repo(repo_path)
                    ticket_pr = repo.get_pull(int(ticket))
                    possibilities.append(ticket_pr)
                except Exception:
                    pass
            continue  # Future-proofing

    return possibilities