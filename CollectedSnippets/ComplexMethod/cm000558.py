def get_replies(
        creds: RedditCredentials, comment_id: str, post_id: str, limit: int
    ) -> list[Comment]:
        client = get_praw(creds)
        post_id = strip_reddit_prefix(post_id)
        comment_id = strip_reddit_prefix(comment_id)

        # Get the submission and find the comment
        submission = client.submission(id=post_id)
        submission.comments.replace_more(limit=0)

        # Find the target comment - filter out MoreComments which don't have .id
        comment = None
        for c in submission.comments.list():
            if isinstance(c, MoreComments):
                continue
            if c.id == comment_id:
                comment = c
                break

        if not comment:
            return []

        # Get direct replies - filter out MoreComments objects
        replies = []
        # CommentForest supports indexing
        for i in range(len(comment.replies)):
            reply = comment.replies[i]
            if isinstance(reply, MoreComments):
                continue
            replies.append(reply)
            if len(replies) >= min(limit, 50):
                break

        return replies