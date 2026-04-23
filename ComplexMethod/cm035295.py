def download_pr_metadata(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str], list[ReviewThread], list[str]]:
        """Run a GraphQL query against the GitHub API for information.

        Retrieves information about:
            1. unresolved review comments
            2. referenced issues the pull request would close

        Args:
            pull_number: The number of the pull request to query.
            comment_id: Optional ID of a specific comment to focus on.
            query: The GraphQL query as a string.
            variables: A dictionary of variables for the query.
            token: Your GitHub personal access token.

        Returns:
            The JSON response from the GitHub API.
        """
        # Using graphql as REST API doesn't indicate resolved status for review comments
        # TODO: grabbing the first 10 issues, 100 review threads, and 100 coments; add pagination to retrieve all
        query = """
                query($owner: String!, $repo: String!, $pr: Int!) {
                    repository(owner: $owner, name: $repo) {
                        pullRequest(number: $pr) {
                            closingIssuesReferences(first: 10) {
                                edges {
                                    node {
                                        body
                                        number
                                    }
                                }
                            }
                            url
                            reviews(first: 100) {
                                nodes {
                                    body
                                    state
                                    fullDatabaseId
                                }
                            }
                            reviewThreads(first: 100) {
                                edges{
                                    node{
                                        id
                                        isResolved
                                        comments(first: 100) {
                                            totalCount
                                            nodes {
                                                body
                                                path
                                                fullDatabaseId
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """

        variables = {'owner': self.owner, 'repo': self.repo, 'pr': pull_number}

        url = self.get_graphql_url()
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }

        response = httpx.post(
            url, json={'query': query, 'variables': variables}, headers=headers
        )
        response.raise_for_status()
        response_json = response.json()

        # Parse the response to get closing issue references and unresolved review comments
        pr_data = (
            response_json.get('data', {}).get('repository', {}).get('pullRequest', {})
        )

        # Get closing issues
        closing_issues = pr_data.get('closingIssuesReferences', {}).get('edges', [])
        closing_issues_bodies = [issue['node']['body'] for issue in closing_issues]
        closing_issue_numbers = [
            issue['node']['number'] for issue in closing_issues
        ]  # Extract issue numbers

        # Get review comments
        reviews = pr_data.get('reviews', {}).get('nodes', [])
        if comment_id is not None:
            reviews = [
                review
                for review in reviews
                if int(review['fullDatabaseId']) == comment_id
            ]
        review_bodies = [review['body'] for review in reviews]

        # Get unresolved review threads
        review_threads = []
        thread_ids = []  # Store thread IDs; agent replies to the thread
        raw_review_threads = pr_data.get('reviewThreads', {}).get('edges', [])
        for thread in raw_review_threads:
            node = thread.get('node', {})
            if not node.get(
                'isResolved', True
            ):  # Check if the review thread is unresolved
                id = node.get('id')
                thread_contains_comment_id = False
                my_review_threads = node.get('comments', {}).get('nodes', [])
                message = ''
                files = []
                for i, review_thread in enumerate(my_review_threads):
                    if (
                        comment_id is not None
                        and int(review_thread['fullDatabaseId']) == comment_id
                    ):
                        thread_contains_comment_id = True

                    if (
                        i == len(my_review_threads) - 1
                    ):  # Check if it's the last thread in the thread
                        if len(my_review_threads) > 1:
                            message += '---\n'  # Add "---" before the last message if there's more than one thread
                        message += 'latest feedback:\n' + review_thread['body'] + '\n'
                    else:
                        message += (
                            review_thread['body'] + '\n'
                        )  # Add each thread in a new line

                    file = review_thread.get('path')
                    if file and file not in files:
                        files.append(file)

                if comment_id is None or thread_contains_comment_id:
                    unresolved_thread = ReviewThread(comment=message, files=files)
                    review_threads.append(unresolved_thread)
                    thread_ids.append(id)

        return (
            closing_issues_bodies,
            closing_issue_numbers,
            review_bodies,
            review_threads,
            thread_ids,
        )