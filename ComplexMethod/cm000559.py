async def run(
        self, input_data: Input, *, credentials: RedditCredentials, **kwargs
    ) -> BlockOutput:
        try:
            redditor = self.get_user_info(credentials, input_data.username)
            moderated = self.get_moderated_subreddits(credentials, input_data.username)

            # Extract moderated subreddit names
            moderated_subreddits = [sub.display_name for sub in moderated]

            # Get profile subreddit info if available
            profile_subreddit = None
            if hasattr(redditor, "subreddit") and redditor.subreddit:
                try:
                    profile_subreddit = RedditUserProfileSubreddit(
                        name=redditor.subreddit.display_name,
                        title=redditor.subreddit.title or "",
                        public_description=redditor.subreddit.public_description or "",
                        subscribers=redditor.subreddit.subscribers or 0,
                        over_18=(
                            redditor.subreddit.over18
                            if hasattr(redditor.subreddit, "over18")
                            else False
                        ),
                    )
                except Exception:
                    # Profile subreddit may not be accessible
                    pass

            user_info = RedditUserInfo(
                username=redditor.name,
                user_id=redditor.id,
                comment_karma=redditor.comment_karma,
                link_karma=redditor.link_karma,
                total_karma=redditor.total_karma,
                created_utc=redditor.created_utc,
                is_gold=redditor.is_gold,
                is_mod=redditor.is_mod,
                has_verified_email=redditor.has_verified_email,
                moderated_subreddits=moderated_subreddits,
                profile_subreddit=profile_subreddit,
            )
            yield "user", user_info
            yield "username", input_data.username
        except Exception as e:
            yield "error", str(e)