async def save_full_pr(self, openhands_pr: OpenhandsPR) -> None:
        """
        Save PR information including metadata and commit details using GraphQL

        Saves:
        - Repo metadata (repo name, languages, contributors)
        - PR metadata (number, title, body, author, comments)
        - Commit information (sha, authors, message, stats)
        - Merge status
        - Num openhands commits
        - Num openhands review comments
        """
        pr_number = openhands_pr.pr_number
        if openhands_pr.installation_id is None:
            logger.warning(
                f'Skipping PR {openhands_pr.repo_name}#{pr_number}: missing installation_id'
            )
            return
        installation_id = int(openhands_pr.installation_id)
        repo_id = openhands_pr.repo_id

        # Get installation token and create Github client
        # This will fail if the user decides to revoke OpenHands' access to their repo
        # In this case, we will simply return when the exception occurs
        # This will not lead to infinite loops when processing PRs as we log number of attempts and cap max attempts independently from this
        try:
            installation_token = self._get_installation_access_token(installation_id)
        except Exception as e:
            logger.warning(
                f'Failed to generate token for {openhands_pr.repo_name}: {e}'
            )
            return

        gh_client = GithubServiceImpl(token=SecretStr(installation_token))

        # Get the new format GraphQL node ID
        node_id = await self._get_repo_node_id(repo_id, gh_client)

        # Initialize data structures
        commits: list[dict] = []
        pr_comments: list[dict] = []
        review_comments: list[dict] = []
        pr_data = None
        repo_data = None

        # Pagination cursors
        commits_after = None
        comments_after = None
        reviews_after = None

        # Fetch all data with pagination
        while True:
            variables = {
                'nodeId': node_id,
                'pr_number': pr_number,
                'commits_after': commits_after,
                'comments_after': comments_after,
                'reviews_after': reviews_after,
            }

            try:
                result = await gh_client.execute_graphql_query(
                    PR_QUERY_BY_NODE_ID, variables
                )
                if not result.get('data', {}).get('node', {}).get('pullRequest'):
                    break

                pr_data = result['data']['node']['pullRequest']
                repo_data = result['data']['node']

                # Process data from this page using modular methods
                self._process_commits_page(pr_data, commits)
                self._process_pr_comments_page(pr_data, pr_comments)
                self._process_review_comments_page(pr_data, review_comments)

                # Check pagination for all three types
                has_more_commits = (
                    pr_data.get('commits', {})
                    .get('pageInfo', {})
                    .get('hasNextPage', False)
                )
                has_more_comments = (
                    pr_data.get('comments', {})
                    .get('pageInfo', {})
                    .get('hasNextPage', False)
                )
                has_more_reviews = (
                    pr_data.get('reviews', {})
                    .get('pageInfo', {})
                    .get('hasNextPage', False)
                )

                # Update cursors
                if has_more_commits:
                    commits_after = (
                        pr_data.get('commits', {}).get('pageInfo', {}).get('endCursor')
                    )
                else:
                    commits_after = None

                if has_more_comments:
                    comments_after = (
                        pr_data.get('comments', {}).get('pageInfo', {}).get('endCursor')
                    )
                else:
                    comments_after = None

                if has_more_reviews:
                    reviews_after = (
                        pr_data.get('reviews', {}).get('pageInfo', {}).get('endCursor')
                    )
                else:
                    reviews_after = None

                # Continue if there's more data to fetch
                if not (has_more_commits or has_more_comments or has_more_reviews):
                    break

            except Exception:
                logger.warning('Error fetching PR data', exc_info=True)
                return

        if not pr_data or not repo_data:
            return

        # Count OpenHands activity using modular method
        (
            openhands_commit_count,
            openhands_review_comment_count,
            openhands_general_comment_count,
        ) = self._count_openhands_activity(commits, review_comments, pr_comments)

        logger.info(
            f'[Github]: PR #{pr_number} - OpenHands commits: {openhands_commit_count}, review comments: {openhands_review_comment_count}, general comments: {openhands_general_comment_count}'
        )
        logger.info(
            f'[Github]: PR #{pr_number} - Total collected: {len(commits)} commits, {len(pr_comments)} PR comments, {len(review_comments)} review comments'
        )

        # Build final data structure using modular method
        data = self._build_final_data_structure(
            repo_data,
            pr_data or {},
            commits,
            pr_comments,
            review_comments,
            openhands_commit_count,
            openhands_review_comment_count,
            openhands_general_comment_count,
        )

        # Update the OpenhandsPR object with OpenHands statistics
        store = OpenhandsPRStore.get_instance()
        openhands_helped_author = openhands_commit_count > 0

        # Update the PR with OpenHands statistics
        update_success = await store.update_pr_openhands_stats(
            repo_id=repo_id,
            pr_number=pr_number,
            original_updated_at=openhands_pr.updated_at,
            openhands_helped_author=openhands_helped_author,
            num_openhands_commits=openhands_commit_count,
            num_openhands_review_comments=openhands_review_comment_count,
            num_openhands_general_comments=openhands_general_comment_count,
        )

        if not update_success:
            logger.warning(
                f'[Github]: Failed to update OpenHands stats for PR #{pr_number} in repo {repo_id} - PR may have been modified concurrently'
            )

        # Save to file
        file_name = self._create_file_name(
            path=self.full_saved_pr_path,
            repo_id=repo_id,
            number=pr_number,
            conversation_id=None,
        )
        self._save_data(file_name, data)
        logger.info(
            f'[Github]: Saved full PR #{pr_number} for repo {repo_id} with OpenHands stats: commits={openhands_commit_count}, reviews={openhands_review_comment_count}, general_comments={openhands_general_comment_count}, helped={openhands_helped_author}'
        )