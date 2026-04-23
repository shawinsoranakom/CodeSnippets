def cmd_list(args):
    search = "sort:updated-asc"
    if args.older_than:
        cutoff = parse_older_than(args.older_than)
        search += f" updated:<{cutoff.isoformat()}"

    labels = args.label or [None]
    if len(labels) == 1:
        issues = gh_issue_list(search, labels[0], args.limit)
    else:
        # Query per label and merge (gh -l does AND, we want OR)
        seen = set()
        issues = []
        for label in labels:
            for issue in gh_issue_list(search, label, args.limit):
                if issue["number"] not in seen:
                    seen.add(issue["number"])
                    issues.append(issue)
        issues.sort(key=lambda i: i["updatedAt"])
        issues = issues[: args.limit]

    for issue in issues:
        issue_labels = ", ".join(l["name"] for l in issue["labels"])
        print(
            f"#{issue['number']:>6}  {issue['updatedAt'][:10]}  {issue['title'][:80]}"
        )
        print(f"         {issue['url']}")
        if issue_labels:
            print(f"         labels: {issue_labels}")

    # Get total count via GitHub search API
    base_query = "repo:pytorch/pytorch is:issue is:open"
    if args.older_than:
        cutoff = parse_older_than(args.older_than)
        base_query += f" updated:<{cutoff.isoformat()}"
    if not args.label:
        total = gh_issue_count(base_query)
    elif len(args.label) == 1:
        total = gh_issue_count(base_query + f' label:"{args.label[0]}"')
    else:
        # Sum per-label counts (may slightly overcount shared issues)
        total = 0
        for label in args.label:
            count = gh_issue_count(base_query + f' label:"{label}"')
            try:
                total += int(count)
            except ValueError:
                total = "?"
                break
        if isinstance(total, int):
            total = f"~{total}"
    print(f"\nShowing {len(issues)} of {total} issues.")