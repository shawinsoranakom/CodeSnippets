def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues from Azure DevOps and convert them to the Issue model."""
        if issue_numbers is None:
            # Download all issues
            work_items = self.download_issues()
        else:
            # Download specific issues
            work_items = []
            for issue_number in issue_numbers:
                work_item_url = f'{self.work_items_api_url}/workitems/{issue_number}?api-version=7.1&$expand=all'

                response = httpx.get(work_item_url, headers=self.get_headers())
                response.raise_for_status()

                work_items.append(response.json())

        issues = []
        for work_item in work_items:
            # Get basic issue information
            issue_number = work_item.get('id')
            title = work_item.get('fields', {}).get('System.Title', '')
            description = work_item.get('fields', {}).get('System.Description', '')

            # Get comments
            thread_comments = self.get_issue_comments(issue_number, comment_id)

            # Check if this is a pull request work item
            is_pr = False
            pr_number = None
            head_branch = None
            base_branch = None

            # Look for PR links in the work item relations
            for relation in work_item.get('relations', []):
                if relation.get(
                    'rel'
                ) == 'ArtifactLink' and 'pullrequest' in relation.get('url', ''):
                    is_pr = True
                    # Extract PR number from URL
                    pr_url = relation.get('url', '')
                    pr_match = re.search(r'pullRequests/(\d+)', pr_url)
                    if pr_match:
                        pr_number = int(pr_match.group(1))
                    break

            # If this is a PR, get the branch information
            if is_pr and pr_number:
                pr_url = f'{self.repo_api_url}/pullRequests/{pr_number}?api-version=7.1'

                pr_response = httpx.get(pr_url, headers=self.get_headers())
                pr_response.raise_for_status()

                pr_data = pr_response.json()
                head_branch = pr_data.get('sourceRefName', '').replace(
                    'refs/heads/', ''
                )
                base_branch = pr_data.get('targetRefName', '').replace(
                    'refs/heads/', ''
                )

                # Get PR review comments
                review_comments = []
                review_threads = []

                threads_url = f'{self.repo_api_url}/pullRequests/{pr_number}/threads?api-version=7.1'

                threads_response = httpx.get(threads_url, headers=self.get_headers())
                threads_response.raise_for_status()

                threads = threads_response.json().get('value', [])

                for thread in threads:
                    thread_comments = [
                        comment.get('content', '')
                        for comment in thread.get('comments', [])
                    ]
                    review_comments.extend(thread_comments)

                    # Get files associated with this thread
                    thread_files = []
                    if thread.get('threadContext', {}).get('filePath'):
                        thread_files.append(
                            thread.get('threadContext', {}).get('filePath')
                        )

                    if thread_comments:
                        review_threads.append(
                            ReviewThread(
                                comment='\n'.join(thread_comments),
                                files=thread_files,
                            )
                        )

            # Create the Issue object
            issue = Issue(
                owner=self.owner,
                repo=self.repository,
                number=issue_number,
                title=title,
                body=description,
                thread_comments=thread_comments,
                closing_issues=None,
                review_comments=review_comments if is_pr else None,
                review_threads=review_threads if is_pr else None,
                thread_ids=None,
                head_branch=head_branch,
                base_branch=base_branch,
            )

            issues.append(issue)

        return issues