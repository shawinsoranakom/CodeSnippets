def load_from_checkpoint(
        self,
        start: SecondsSinceUnixEpoch,
        end: SecondsSinceUnixEpoch,
        checkpoint: BitbucketConnectorCheckpoint,
    ) -> CheckpointOutput[BitbucketConnectorCheckpoint]:
        """Resumable PR ingestion across repos and pages within a time window.

        Yields Documents (or ConnectorFailure for per-PR mapping failures) and returns
        an updated checkpoint that records repo position and next page URL.
        """
        new_checkpoint = copy.deepcopy(checkpoint)

        with self._client() as client:
            # Materialize target repositories once
            if not new_checkpoint.repos_queue:
                # Preserve explicit order; otherwise ensure deterministic ordering
                repos_list = list(self._iter_target_repositories(client))
                new_checkpoint.repos_queue = sorted(set(repos_list))
                new_checkpoint.current_repo_index = 0
                new_checkpoint.next_url = None

            repos = new_checkpoint.repos_queue
            if not repos or new_checkpoint.current_repo_index >= len(repos):
                new_checkpoint.has_more = False
                return new_checkpoint

            repo_slug = repos[new_checkpoint.current_repo_index]

            first_page_params = self._build_params(
                fields=PR_LIST_RESPONSE_FIELDS,
                start=start,
                end=end,
            )

            def _on_page(next_url: str | None) -> None:
                new_checkpoint.next_url = next_url

            for pr in self._iter_pull_requests_for_repo(
                client,
                repo_slug,
                params=first_page_params,
                start_url=new_checkpoint.next_url,
                on_page=_on_page,
            ):
                try:
                    document = map_pr_to_document(pr, self.workspace, repo_slug)
                    yield document
                except Exception as e:
                    pr_id = pr.get("id")
                    pr_link = (
                        f"https://bitbucket.org/{self.workspace}/{repo_slug}/pull-requests/{pr_id}"
                        if pr_id is not None
                        else None
                    )
                    yield ConnectorFailure(
                        failed_document=DocumentFailure(
                            document_id=(
                                f"{DocumentSource.BITBUCKET.value}:{self.workspace}:{repo_slug}:pr:{pr_id}"
                                if pr_id is not None
                                else f"{DocumentSource.BITBUCKET.value}:{self.workspace}:{repo_slug}:pr:unknown"
                            ),
                            document_link=pr_link,
                        ),
                        failure_message=f"Failed to process Bitbucket PR: {e}",
                        exception=e,
                    )

            # Advance to next repository (if any) and set has_more accordingly
            new_checkpoint.current_repo_index += 1
            new_checkpoint.next_url = None
            new_checkpoint.has_more = new_checkpoint.current_repo_index < len(repos)

        return new_checkpoint