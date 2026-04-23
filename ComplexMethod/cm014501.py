def get_comment_by_id(self, database_id: int) -> GitHubComment:
        if self.comments is None:
            # Fastpath - try searching in partial prefetched comments
            for node in self.info["comments"]["nodes"]:
                comment = self._comment_from_node(node)
                if comment.database_id == database_id:
                    return comment

        for comment in self.get_comments():
            if comment.database_id == database_id:
                return comment

        # The comment could have actually been a review left on the PR (the message written alongside the review).
        # (This is generally done to trigger the merge right when a comment is left)
        # Check those review comments to see if one of those was the comment in question.
        for node in self.info["reviews"]["nodes"]:
            # These review comments contain all the fields regular comments need
            comment = self._comment_from_node(node)
            if comment.database_id == database_id:
                return comment

        raise RuntimeError(f"Comment with id {database_id} not found")