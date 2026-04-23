def main(verbose=False):
    branch = get_release_branch_name()
    checkout_branch(branch)
    prs = get_prs_by_label(LABEL)
    # Attach commit timestamps
    for pr in prs:
        sha = pr.get("oid")
        if sha:
            pr["timestamp"] = get_commit_timestamp(sha)
        else:
            print("\n" + "=" * 80)
            print(f"[WARNING] PR #{pr['number']} ({sha}) is NOT in main!")
            print("[WARNING] A core maintainer must review this before cherry-picking.")
            print("=" * 80 + "\n")
    # Sort by commit timestamp (ascending)
    prs = [pr for pr in prs if pr.get("timestamp") is not None]
    prs.sort(key=lambda pr: pr["timestamp"])
    for pr in prs:
        sha = pr.get("oid")
        if sha:
            if commit_in_history(sha):
                if verbose:
                    print(f"[INFO] PR #{pr['number']} ({pr['title']}) already in history. Skipping.")
            else:
                print(f"[INFO] PR #{pr['number']} ({pr['title']}) not in history. Cherry-picking...")
                cherry_pick_commit(sha)