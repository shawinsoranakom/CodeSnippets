def normalize_pr_url(pr, allow_non_ansible_ansible=False, only_number=False):
    """
    Given a PullRequest, or a string containing a PR number, PR URL,
    or internal PR URL (e.g. ansible-collections/community.general#1234),
    return either a full github URL to the PR (if only_number is False),
    or an int containing the PR number (if only_number is True).

    Throws if it can't parse the input.
    """
    if isinstance(pr, PullRequest):
        return pr.html_url

    if pr.isnumeric():
        if only_number:
            return int(pr)
        return 'https://github.com/ansible/ansible/pull/{0}'.format(pr)

    # Allow for forcing ansible/ansible
    if not allow_non_ansible_ansible and 'ansible/ansible' not in pr:
        raise Exception('Non ansible/ansible repo given where not expected')

    re_match = PULL_HTTP_URL_RE.match(pr)
    if re_match:
        if only_number:
            return int(re_match.group('ticket'))
        return pr

    re_match = PULL_URL_RE.match(pr)
    if re_match:
        if only_number:
            return int(re_match.group('ticket'))
        return 'https://github.com/{0}/{1}/pull/{2}'.format(
            re_match.group('user'),
            re_match.group('repo'),
            re_match.group('ticket'))

    raise Exception('Did not understand given PR')