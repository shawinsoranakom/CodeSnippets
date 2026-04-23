def rebase_ghstack_onto(
    pr: GitHubPR, repo: GitRepo, onto_branch: str, dry_run: bool = False
) -> bool:
    if (
        subprocess.run(
            [sys.executable, "-m", "ghstack", "--help"],
            capture_output=True,
            check=False,
        ).returncode
        != 0
    ):
        subprocess.run([sys.executable, "-m", "pip", "install", "ghstack"], check=True)
    orig_ref = f"{re.sub(r'/head$', '/orig', pr.head_ref())}"

    repo.fetch(orig_ref, orig_ref)
    repo._run_git("rebase", onto_branch, orig_ref)

    if repo.rev_parse(orig_ref) == repo.rev_parse(onto_branch):
        raise Exception(SAME_SHA_ERROR)  # noqa: TRY002

    # steal the identity of the committer of the commit on the orig branch
    email = repo._run_git("log", orig_ref, "--pretty=format:%ae", "-1")
    name = repo._run_git("log", orig_ref, "--pretty=format:%an", "-1")
    repo._run_git("config", "--global", "user.email", email)
    repo._run_git("config", "--global", "user.name", name)

    os.environ["OAUTH_TOKEN"] = os.environ["GITHUB_TOKEN"]
    with open(".ghstackrc", "w+") as f:
        f.write(
            "[ghstack]\n"
            + "github_url=github.com\n"
            + "github_username=pytorchmergebot\n"
            + "remote_name=origin"
        )

    if dry_run:
        print("Don't know how to dry-run ghstack")
        return False
    else:
        ghstack_result = subprocess.run(["ghstack"], capture_output=True, check=True)
        push_result = ghstack_result.stdout.decode("utf-8")
        print(push_result)
        if ghstack_result.returncode != 0:
            print(ghstack_result.stderr.decode("utf-8"))
            raise Exception(f"\n```{push_result}```")  # noqa: TRY002
        # The contents of a successful push result should look like:
        # Summary of changes (ghstack 0.6.0)

        #  - Updated https://github.com/clee2000/random-testing-public/pull/2
        #  - Updated https://github.com/clee2000/random-testing-public/pull/1

        # Facebook employees can import your changes by running
        # (on a Facebook machine):

        #     ghimport -s https://github.com/clee2000/random-testing-public/pull/2

        # If you want to work on this diff stack on another machine:

        #     ghstack checkout https://github.com/clee2000/random-testing-public/pull/2
        org, project = repo.gh_owner_and_name()
        for line in push_result.splitlines():
            if "Updated" in line:
                pr_num = int(line.split("/")[-1])
                if pr_num != pr.pr_num:
                    gh_post_comment(
                        pr.org,
                        pr.project,
                        pr_num,
                        f"Rebased `{orig_ref}` onto `{onto_branch}` because #{pr.pr_num} was rebased, "
                        "please pull locally before adding more changes (for example, via `ghstack "
                        + f"checkout https://github.com/{org}/{project}/pull/{pr_num}`)",
                        dry_run=dry_run,
                    )
                else:
                    gh_post_comment(
                        pr.org,
                        pr.project,
                        pr_num,
                        f"Successfully rebased `{orig_ref}` onto `{onto_branch}`, please pull locally "
                        + "before adding more changes (for example, via `ghstack "
                        + f"checkout https://github.com/{org}/{project}/pull/{pr.pr_num}`)",
                        dry_run=dry_run,
                    )

        if (
            f"Skipped https://github.com/{org}/{project}/pull/{pr.pr_num}"
            in push_result
        ):
            post_already_uptodate(pr, repo, onto_branch, dry_run)
            return False
        return True