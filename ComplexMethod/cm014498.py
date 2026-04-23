def main() -> None:
    args = parse_args()
    repo = GitRepo(get_git_repo_dir(), get_git_remote_name())
    org, project = repo.gh_owner_and_name()
    pr = GitHubPR(org, project, args.pr_num)

    def handle_exception(e: Exception, title: str = "Merge failed") -> None:
        exception = f"**Reason**: {e}"

        failing_rule = None
        if isinstance(e, MergeRuleFailedError):
            failing_rule = e.rule.name if e.rule else None

        internal_debugging = ""
        run_url = os.getenv("GH_RUN_URL")
        if run_url is not None:
            # Hide this behind a collapsed bullet since it's not helpful to most devs
            internal_debugging = "\n".join(
                line
                for line in (
                    "<details><summary>Details for Dev Infra team</summary>",
                    f'Raised by <a href="{run_url}">workflow job</a>\n',
                    f"Failing merge rule: {failing_rule}" if failing_rule else "",
                    "</details>",
                )
                if line
            )  # ignore empty lines during the join

        msg = "\n".join((f"## {title}", f"{exception}", "", f"{internal_debugging}"))

        gh_post_pr_comment(org, project, args.pr_num, msg, dry_run=args.dry_run)
        import traceback

        traceback.print_exc()

    if args.revert:
        try:
            gh_post_pr_comment(
                org,
                project,
                args.pr_num,
                get_revert_message(org, project, pr.pr_num),
                args.dry_run,
            )
            try_revert(
                repo,
                pr,
                dry_run=args.dry_run,
                comment_id=args.comment_id,
                reason=args.reason,
            )
        except Exception as e:
            handle_exception(e, f"Reverting PR {args.pr_num} failed")
        return

    if pr.is_closed():
        gh_post_pr_comment(
            org,
            project,
            args.pr_num,
            f"Can't merge closed PR #{args.pr_num}",
            dry_run=args.dry_run,
        )
        return

    if pr.is_cross_repo() and pr.is_ghstack_pr():
        gh_post_pr_comment(
            org,
            project,
            args.pr_num,
            "Cross-repo ghstack merges are not supported",
            dry_run=args.dry_run,
        )
        return
    if not pr.is_ghstack_pr() and pr.base_ref() != pr.default_branch():
        gh_post_pr_comment(
            org,
            project,
            args.pr_num,
            f"PR targets {pr.base_ref()} rather than {pr.default_branch()}, refusing merge request",
            dry_run=args.dry_run,
        )
        return

    if args.check_mergeability:
        if pr.is_ghstack_pr():
            get_ghstack_prs(repo, pr)  # raises error if out of sync
        pr.merge_changes_locally(
            repo,
            skip_mandatory_checks=True,
            skip_all_rule_checks=True,
        )
        return

    if not args.force and pr.has_invalid_submodule_updates():
        message = (
            f"This PR updates submodules {', '.join(pr.get_changed_submodules())}\n"
        )
        message += '\nIf those updates are intentional, please add "submodule" keyword to PR title/description.'
        gh_post_pr_comment(org, project, args.pr_num, message, dry_run=args.dry_run)
        return
    try:
        # Ensure comment id is set, else fail
        if not args.comment_id:
            raise ValueError(
                "Comment ID is required for merging PRs, please provide it using --comment-id"
            )

        merge(
            pr,
            repo,
            comment_id=args.comment_id,
            dry_run=args.dry_run,
            skip_mandatory_checks=args.force,
            ignore_current=args.ignore_current,
        )
    except Exception as e:
        handle_exception(e)

        if args.comment_id and args.pr_num:
            # Finally, upload the record to s3, we don't have access to the
            # list of pending and failed checks here, but they are not really
            # needed at the moment
            save_merge_record(
                comment_id=args.comment_id,
                pr_num=args.pr_num,
                owner=org,
                project=project,
                author=pr.get_author(),
                pending_checks=[],
                failed_checks=[],
                ignore_current_checks=[],
                broken_trunk_checks=[],
                flaky_checks=[],
                unstable_checks=[],
                last_commit_sha=pr.last_commit_sha(default=""),
                merge_base_sha=pr.get_merge_base(),
                is_failed=True,
                skip_mandatory_checks=args.force,
                ignore_current=args.ignore_current,
                error=str(e),
            )
        else:
            print("Missing comment ID or PR number, couldn't upload to s3")
    finally:
        if not args.check_mergeability:
            gh_remove_label(
                org, project, args.pr_num, MERGE_IN_PROGRESS_LABEL, args.dry_run
            )