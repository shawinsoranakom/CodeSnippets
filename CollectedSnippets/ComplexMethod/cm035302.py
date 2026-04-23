def download_pr_metadata(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str] | None, list[ReviewThread], list[str]]:
        """Run a GraphQL query against the Gitlab API for information.

        Retrieves information about:
            1. unresolved review comments
            2. referenced issues the pull request would close

        Args:
            pull_number: The number of the pull request to query.
            comment_id: Optional ID of a specific comment to focus on.
            query: The GraphQL query as a string.
            variables: A dictionary of variables for the query.
            token: Your Gitlab personal access token.

        Returns:
            The JSON response from the Gitlab API.
        """
        # Using graphql as REST API doesn't indicate resolved status for review comments
        # TODO: grabbing the first 10 issues, 100 review threads, and 100 coments; add pagination to retrieve all
        response = httpx.get(
            f'{self.base_url}/merge_requests/{pull_number}/related_issues',
            headers=self.headers,
        )
        response.raise_for_status()
        closing_issues = response.json()
        closing_issues_bodies = [issue['description'] for issue in closing_issues]
        closing_issue_numbers = [
            issue['iid'] for issue in closing_issues
        ]  # Extract issue numbers

        query = """
                query($projectPath: ID!, $pr: String!) {
                    project(fullPath: $projectPath) {
                        mergeRequest(iid: $pr) {
                            webUrl
                            discussions(first: 100) {
                                edges {
                                    node {
                                        id
                                        resolved
                                        resolvable
                                        notes(first: 100) {
                                            nodes {
                                                body
                                                id
                                                position {
                                                    filePath
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            """

        project_path = f'{self.owner}/{self.repo}'
        variables = {'projectPath': project_path, 'pr': str(pull_number)}

        response = httpx.post(
            self.get_graphql_url(),
            json={'query': query, 'variables': variables},
            headers=self.headers,
        )
        response.raise_for_status()
        response_json = response.json()

        # Parse the response to get closing issue references and unresolved review comments
        pr_data = (
            response_json.get('data', {}).get('project', {}).get('mergeRequest', {})
        )

        # Get review comments
        review_bodies = None

        # Get unresolved review threads
        review_threads = []
        thread_ids = []  # Store thread IDs; agent replies to the thread
        raw_review_threads = pr_data.get('discussions', {}).get('edges', [])

        for thread in raw_review_threads:
            node = thread.get('node', {})
            if not node.get('resolved', True) and node.get(
                'resolvable', True
            ):  # Check if the review thread is unresolved
                id = node.get('id')
                thread_contains_comment_id = False
                my_review_threads = node.get('notes', {}).get('nodes', [])
                message = ''
                files = []
                for i, review_thread in enumerate(my_review_threads):
                    if (
                        comment_id is not None
                        and int(review_thread['id'].split('/')[-1]) == comment_id
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

                    file = review_thread.get('position', {})
                    file = file.get('filePath') if file is not None else None
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