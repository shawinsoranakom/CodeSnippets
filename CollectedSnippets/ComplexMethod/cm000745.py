async def create_review(
        credentials: GithubCredentials,
        repo: str,
        pr_number: int,
        body: str,
        event: ReviewEvent,
        create_as_draft: bool,
        comments: Optional[List[Input.ReviewComment]] = None,
    ) -> tuple[int, str, str]:
        api = get_api(credentials, convert_urls=False)

        # GitHub API endpoint for creating reviews
        reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"

        # Get commit_id if we have comments
        commit_id = None
        if comments:
            # Get PR details to get the head commit for inline comments
            pr_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            pr_response = await api.get(pr_url)
            pr_data = pr_response.json()
            commit_id = pr_data["head"]["sha"]

        # Prepare the request data
        # If create_as_draft is True, omit the event field (creates a PENDING review)
        # Otherwise, use the actual event value which will auto-submit the review
        data: dict[str, Any] = {"body": body}

        # Add commit_id if we have it
        if commit_id:
            data["commit_id"] = commit_id

        # Add comments if provided
        if comments:
            # Process comments to ensure they have the required fields
            processed_comments = []
            for comment in comments:
                comment_data: dict = {
                    "path": comment.get("path", ""),
                    "body": comment.get("body", ""),
                }
                # Add position or line
                # Note: For review comments, only position is supported (not line/side)
                if "position" in comment and comment.get("position") is not None:
                    comment_data["position"] = comment.get("position")
                elif "line" in comment and comment.get("line") is not None:
                    # Note: Using line as position - may not work correctly
                    # Position should be calculated from the diff
                    comment_data["position"] = comment.get("line")

                # Note: side, start_line, and start_side are NOT supported for review comments
                # They are only for standalone PR comments

                processed_comments.append(comment_data)

            data["comments"] = processed_comments

        if not create_as_draft:
            # Only add event field if not creating a draft
            data["event"] = event.value

        # Create the review
        response = await api.post(reviews_url, json=data)
        review_data = response.json()

        return review_data["id"], review_data["state"], review_data["html_url"]