async def create_issue(
        repo_name: str,
        title: str,
        body: Optional[str] = None,
        assignee: NamedUser | Optional[str] = None,
        milestone: Optional[Milestone] = None,
        labels: list[Label] | Optional[list[str]] = None,
        assignees: Optional[list[str]] | list[NamedUser] = None,
        access_token: Optional[str] = None,
        auth: Optional[Auth] = None,
    ) -> Issue:
        """
        Creates an issue in the specified repository.

        Args:
            repo_name (str): The full repository name (user/repo) where the issue will be created.
            title (str): The title of the issue.
            body (Optional[str], optional): The body of the issue. Defaults to None.
            assignee (Union[NamedUser, str], optional): The assignee for the issue, either as a NamedUser object or their username. Defaults to None.
            milestone (Optional[Milestone], optional): The milestone to associate with the issue. Defaults to None.
            labels (Union[list[Label], list[str]], optional): The labels to associate with the issue, either as Label objects or their names. Defaults to None.
            assignees (Union[list[str], list[NamedUser]], optional): The list of usernames or NamedUser objects to assign to the issue. Defaults to None.
            access_token (Optional[str], optional): The access token for authentication. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
            auth (Optional[Auth], optional): The authentication method. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`

        Returns:
            Issue: The created issue object.
        """
        body = body or NotSet
        assignee = assignee or NotSet
        milestone = milestone or NotSet
        labels = labels or NotSet
        assignees = assignees or NotSet
        if not auth and not access_token:
            raise ValueError('`access_token` is invalid. Visit: "https://github.com/settings/tokens"')
        auth = auth or Auth.Token(access_token)
        g = Github(auth=auth)

        repo = g.get_repo(repo_name)
        x_ratelimit_remaining = repo.raw_headers.get("x-ratelimit-remaining")
        if (
            x_ratelimit_remaining
            and bool(re.match(r"^-?\d+$", x_ratelimit_remaining))
            and int(x_ratelimit_remaining) <= 0
        ):
            raise RateLimitError()
        issue = repo.create_issue(
            title=title,
            body=body,
            assignee=assignee,
            milestone=milestone,
            labels=labels,
            assignees=assignees,
        )
        return issue