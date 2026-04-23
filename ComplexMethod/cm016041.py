def main():
    parser = argparse.ArgumentParser(
        description="Parse cherry-pick comments from a PyTorch GitHub issue"
    )
    parser.add_argument("issue_url", help="GitHub issue URL to parse")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output CSV file path (default: results/cherry_picks_<issue_number>.csv relative to script)",
    )
    parser.add_argument(
        "--commitlist",
        required=True,
        help="Path to commitlist.csv to validate commit hashes against",
    )
    args = parser.parse_args()

    repo, issue_number = parse_issue_url(args.issue_url)
    if args.output:
        output_path = args.output
    else:
        script_dir = Path(__file__).resolve().parent
        results_dir = script_dir / "results"
        results_dir.mkdir(exist_ok=True)
        output_path = str(results_dir / f"cherry_picks_{issue_number}.csv")

    comments = fetch_comments(repo, issue_number)

    rows = []
    for comment in comments:
        comment_id = comment["id"]
        body = comment["body"] or ""

        trunk_prs = extract_trunk_prs(body)
        if not trunk_prs:
            # Comment doesn't contain the trunk PR section — skip
            continue

        if len(trunk_prs) > 1:
            logger.warning(
                f"Comment {comment_id} has {len(trunk_prs)} trunk PRs: "
                + ", ".join(
                    p["pr_number"] or p["raw_commit"] or "N/A" for p in trunk_prs
                )
            )

        for pr_info in trunk_prs:
            pr_number = pr_info["pr_number"]
            raw_commit = pr_info["raw_commit"]
            pr_title = ""
            commit_sha = raw_commit  # Use raw commit if provided

            if pr_number:
                logger.info(f"Fetching info for PR #{pr_number}...")
                pr_title = fetch_pr_title(repo, pr_number)
                commit_sha = fetch_landed_commit(repo, pr_number)

            rows.append(
                {
                    "comment_id": comment_id,
                    "pr_number": pr_number,
                    "pr_title": pr_title,
                    "commit_sha": commit_sha,
                }
            )

    # Validate against commitlist
    commitlist_hashes = set()
    with open(args.commitlist, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if row:
                commitlist_hashes.add(row[0])

    logger.info(f"Loaded {len(commitlist_hashes)} hashes from {args.commitlist}")

    matched = 0
    mismatched = 0
    skipped = 0
    for row in rows:
        sha = row["commit_sha"]
        if not sha:
            skipped += 1
            continue
        # commitlist uses abbreviated hashes; check if any is a prefix of
        # our full hash, or vice versa
        if any(
            sha.startswith(cl_hash) or cl_hash.startswith(sha)
            for cl_hash in commitlist_hashes
        ):
            matched += 1
        else:
            mismatched += 1
            logger.warning(
                f"Commit {sha[:11]} (PR #{row['pr_number'] or 'N/A'}) "
                f"not found in commitlist"
            )

    logger.info(
        f"Commitlist validation: {matched} matched, {mismatched} not found, "
        f"{skipped} skipped (no hash)"
    )

    # Write CSV
    fieldnames = ["comment_id", "pr_number", "pr_title", "commit_sha"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} rows to {output_path}")