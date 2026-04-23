def to_markdown(commit_list: CommitList, category):
    def cleanup_title(commit):
        match = re.match(r"(.*) \(#\d+\)", commit.title)
        if match is None:
            return commit.title
        return match.group(1)

    merge_mapping = defaultdict(list)
    for commit in commit_list.commits:
        if commit.merge_into:
            merge_mapping[commit.merge_into].append(commit)

    cdc = get_commit_data_cache()
    lines = [f"\n## {category}\n"]
    for topic in topics:
        lines.append(f"### {topic}\n")
        commits = commit_list.filter(category=category, topic=topic)
        if "_" in topic:
            commits.extend(
                commit_list.filter(category=category, topic=topic.replace("_", " "))
            )
        if " " in topic:
            commits.extend(
                commit_list.filter(category=category, topic=topic.replace(" ", "_"))
            )
        for commit in commits:
            if commit.merge_into:
                continue
            all_related_commits = merge_mapping[commit.commit_hash] + [commit]
            commit_list_md = ", ".join(
                get_hash_or_pr_url(c) for c in all_related_commits
            )
            result = f"- {cleanup_title(commit)} ({commit_list_md})\n"
            lines.append(result)
    return lines