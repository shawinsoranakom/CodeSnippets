def _fetch_from_github(
        self,
        checkpoint: GithubConnectorCheckpoint,
        start: datetime | None = None,
        end: datetime | None = None,
        include_permissions: bool = False,
    ) -> Generator[Document | ConnectorFailure, None, GithubConnectorCheckpoint]:
        if self.github_client is None:
            raise ConnectorMissingCredentialError("GitHub")

        checkpoint = copy.deepcopy(checkpoint)

        # First run of the connector, fetch all repos and store in checkpoint
        if checkpoint.cached_repo_ids is None:
            repos = []
            if self.repositories:
                if "," in self.repositories:
                    # Multiple repositories specified
                    repos = self.get_github_repos(self.github_client)
                else:
                    # Single repository (backward compatibility)
                    repos = [self.get_github_repo(self.github_client)]
            else:
                # All repositories
                repos = self.get_all_repos(self.github_client)
            if not repos:
                checkpoint.has_more = False
                return checkpoint

            curr_repo = repos.pop()
            checkpoint.cached_repo_ids = [repo.id for repo in repos]
            checkpoint.cached_repo = SerializedRepository(
                id=curr_repo.id,
                headers=curr_repo.raw_headers,
                raw_data=curr_repo.raw_data,
            )
            checkpoint.stage = GithubConnectorStage.PRS
            checkpoint.curr_page = 0
            # save checkpoint with repo ids retrieved
            return checkpoint

        if checkpoint.cached_repo is None:
            raise ValueError("No repo saved in checkpoint")

        # Deserialize the repository from the checkpoint
        repo = deserialize_repository(checkpoint.cached_repo, self.github_client)

        cursor_url_callback = make_cursor_url_callback(checkpoint)
        repo_external_access: ExternalAccess | None = None
        if include_permissions:
            repo_external_access = get_external_access_permission(
                repo, self.github_client
            )
        if self.include_prs and checkpoint.stage == GithubConnectorStage.PRS:
            logging.info(f"Fetching PRs for repo: {repo.name}")

            pr_batch = _get_batch_rate_limited(
                self._pull_requests_func(repo),
                checkpoint.curr_page,
                checkpoint.cursor_url,
                checkpoint.num_retrieved,
                cursor_url_callback,
                self.github_client,
            )
            checkpoint.curr_page += 1  # NOTE: not used for cursor-based fallback
            done_with_prs = False
            num_prs = 0
            pr = None
            for pr in pr_batch:
                num_prs += 1
                # we iterate backwards in time, so at this point we stop processing prs
                if (
                    start is not None
                    and pr.updated_at
                    and pr.updated_at.replace(tzinfo=timezone.utc) <= start
                ):
                    done_with_prs = True
                    break
                # Skip PRs updated after the end date
                if (
                    end is not None
                    and pr.updated_at
                    and pr.updated_at.replace(tzinfo=timezone.utc) > end
                ):
                    continue
                try:
                    yield _convert_pr_to_document(
                        cast(PullRequest, pr), repo_external_access
                    )
                except Exception as e:
                    error_msg = f"Error converting PR to document: {e}"
                    logging.exception(error_msg)
                    yield ConnectorFailure(
                        failed_document=DocumentFailure(
                            document_id=str(pr.id), document_link=pr.html_url
                        ),
                        failure_message=error_msg,
                        exception=e,
                    )
                    continue

            # If we reach this point with a cursor url in the checkpoint, we were using
            # the fallback cursor-based pagination strategy. That strategy tries to get all
            # PRs, so having curosr_url set means we are done with prs. However, we need to
            # return AFTER the checkpoint reset to avoid infinite loops.

            # if we found any PRs on the page and there are more PRs to get, return the checkpoint.
            # In offset mode, while indexing without time constraints, the pr batch
            # will be empty when we're done.
            used_cursor = checkpoint.cursor_url is not None
            if num_prs > 0 and not done_with_prs and not used_cursor:
                return checkpoint

            # if we went past the start date during the loop or there are no more
            # prs to get, we move on to issues
            checkpoint.stage = GithubConnectorStage.ISSUES
            checkpoint.reset()

            if used_cursor:
                # save the checkpoint after changing stage; next run will continue from issues
                return checkpoint

        checkpoint.stage = GithubConnectorStage.ISSUES

        if self.include_issues and checkpoint.stage == GithubConnectorStage.ISSUES:
            logging.info(f"Fetching issues for repo: {repo.name}")

            issue_batch = list(
                _get_batch_rate_limited(
                    self._issues_func(repo),
                    checkpoint.curr_page,
                    checkpoint.cursor_url,
                    checkpoint.num_retrieved,
                    cursor_url_callback,
                    self.github_client,
                )
            )
            checkpoint.curr_page += 1
            done_with_issues = False
            num_issues = 0
            for issue in issue_batch:
                num_issues += 1
                issue = cast(Issue, issue)
                # we iterate backwards in time, so at this point we stop processing prs
                if (
                    start is not None
                    and issue.updated_at.replace(tzinfo=timezone.utc) <= start
                ):
                    done_with_issues = True
                    break
                # Skip PRs updated after the end date
                if (
                    end is not None
                    and issue.updated_at.replace(tzinfo=timezone.utc) > end
                ):
                    continue

                if issue.pull_request is not None:
                    # PRs are handled separately
                    continue

                try:
                    yield _convert_issue_to_document(issue, repo_external_access)
                except Exception as e:
                    error_msg = f"Error converting issue to document: {e}"
                    logging.exception(error_msg)
                    yield ConnectorFailure(
                        failed_document=DocumentFailure(
                            document_id=str(issue.id),
                            document_link=issue.html_url,
                        ),
                        failure_message=error_msg,
                        exception=e,
                    )
                    continue

            # if we found any issues on the page, and we're not done, return the checkpoint.
            # don't return if we're using cursor-based pagination to avoid infinite loops
            if num_issues > 0 and not done_with_issues and not checkpoint.cursor_url:
                return checkpoint

            # if we went past the start date during the loop or there are no more
            # issues to get, we move on to the next repo
            checkpoint.stage = GithubConnectorStage.PRS
            checkpoint.reset()

        checkpoint.has_more = len(checkpoint.cached_repo_ids) > 0
        if checkpoint.cached_repo_ids:
            next_id = checkpoint.cached_repo_ids.pop()
            next_repo = self.github_client.get_repo(next_id)
            checkpoint.cached_repo = SerializedRepository(
                id=next_id,
                headers=next_repo.raw_headers,
                raw_data=next_repo.raw_data,
            )
            checkpoint.stage = GithubConnectorStage.PRS
            checkpoint.reset()

        if checkpoint.cached_repo_ids:
            logging.info(
                f"{len(checkpoint.cached_repo_ids)} checkpoint repos remaining (IDs: {checkpoint.cached_repo_ids})"
            )
        else:
            logging.info("There are no more checkpoint repos left.")

        return checkpoint