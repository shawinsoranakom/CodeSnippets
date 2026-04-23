def get_commit_sha_at_comment(self, comment_id: int) -> str | None:
        """
        Get the PR head commit SHA that was present when a specific comment was posted.
        This ensures we only merge the state of the PR at the time the merge command was issued,
        not any subsequent commits that may have been pushed after.

        Returns None if no head-changing events found before the comment or if the comment was not found.
        """
        head = None

        try:
            for event in iter_issue_timeline_until_comment(
                self.org, self.project, self.pr_num, comment_id
            ):
                etype = event.get("event")
                if etype == "committed":
                    sha = sha_from_committed_event(event)
                    if sha:
                        head = sha
                        print(f"Timeline: Found commit event for SHA {sha}")
                elif etype == "head_ref_force_pushed":
                    sha = sha_from_force_push_after(event)
                    if sha:
                        head = sha
                        print(f"Timeline: Found force push event for SHA {sha}")
                elif etype == "commented":
                    if event.get("id") == comment_id:
                        print(f"Timeline: Found final comment with sha {sha}")
                        return head
        except Exception as e:
            print(
                f"Warning: Failed to reconstruct timeline for comment {comment_id}: {e}"
            )
            return None

        print(f"Did not find comment with id {comment_id} in the PR timeline")
        return None