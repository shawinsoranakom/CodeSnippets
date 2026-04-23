async def create_pull(
        base: str,
        head: str,
        base_repo_name: str,
        head_repo_name: Optional[str] = None,
        *,
        title: Optional[str] = None,
        body: Optional[str] = None,
        maintainer_can_modify: Optional[bool] = None,
        draft: Optional[bool] = None,
        issue: Optional[Issue] = None,
        access_token: Optional[str] = None,
        auth: Optional[Auth] = None,
    ) -> Union[PullRequest, str]:
        """
        Creates a pull request in the specified repository.

        Args:
            base (str): The name of the base branch.
            head (str): The name of the head branch.
            base_repo_name (str): The full repository name (user/repo) where the pull request will be created.
            head_repo_name (Optional[str], optional): The full repository name (user/repo) where the pull request will merge from. Defaults to None.
            title (Optional[str], optional): The title of the pull request. Defaults to None.
            body (Optional[str], optional): The body of the pull request. Defaults to None.
            maintainer_can_modify (Optional[bool], optional): Whether maintainers can modify the pull request. Defaults to None.
            draft (Optional[bool], optional): Whether the pull request is a draft. Defaults to None.
            issue (Optional[Issue], optional): The issue linked to the pull request. Defaults to None.
            access_token (Optional[str], optional): The access token for authentication. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`, `https://github.com/PyGithub/PyGithub/blob/main/doc/examples/Authentication.rst`.
            auth (Optional[Auth], optional): The authentication method. Defaults to None. Visit `https://pygithub.readthedocs.io/en/latest/examples/Authentication.html`

        Returns:
            PullRequest: The created pull request object.
        """
        title = title or NotSet
        body = body or NotSet
        maintainer_can_modify = maintainer_can_modify or NotSet
        draft = draft or NotSet
        issue = issue or NotSet
        if not auth and not access_token:
            raise ValueError('`access_token` is invalid. Visit: "https://github.com/settings/tokens"')
        clone_url = f"https://github.com/{base_repo_name}.git"
        try:
            auth = auth or Auth.Token(access_token)
            g = Github(auth=auth)
            base_repo = g.get_repo(base_repo_name)
            clone_url = base_repo.clone_url
            head_repo = g.get_repo(head_repo_name) if head_repo_name and head_repo_name != base_repo_name else None
            if head_repo:
                user = head_repo.full_name.split("/")[0]
                head = f"{user}:{head}"
            pr = base_repo.create_pull(
                base=base,
                head=head,
                title=title,
                body=body,
                maintainer_can_modify=maintainer_can_modify,
                draft=draft,
                issue=issue,
            )
        except Exception as e:
            logger.warning(f"Pull Request Error: {e}")
            return GitRepository.create_github_pull_url(
                clone_url=clone_url,
                base=base,
                head=head,
                head_repo_name=head_repo_name,
            )
        return pr