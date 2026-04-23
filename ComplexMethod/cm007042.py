def get_video_comments(self) -> DataFrame:
        """Retrieves comments from a YouTube video and returns as DataFrame."""
        try:
            # Extract video ID from URL
            video_id = self._extract_video_id(self.video_url)

            # Use context manager for YouTube API client
            with self.youtube_client() as youtube:
                comments_data = []
                results_count = 0
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(self.API_MAX_RESULTS, self.max_results),
                    order=self.sort_by,
                    textFormat="plainText",
                )

                while request and results_count < self.max_results:
                    response = request.execute()

                    for item in response.get("items", []):
                        if results_count >= self.max_results:
                            break

                        comments = self._process_comment(
                            item, include_metrics=self.include_metrics, include_replies=self.include_replies
                        )
                        comments_data.extend(comments)
                        results_count += 1

                    # Get the next page if available and needed
                    if "nextPageToken" in response and results_count < self.max_results:
                        request = youtube.commentThreads().list(
                            part="snippet,replies",
                            videoId=video_id,
                            maxResults=min(self.API_MAX_RESULTS, self.max_results - results_count),
                            order=self.sort_by,
                            textFormat="plainText",
                            pageToken=response["nextPageToken"],
                        )
                    else:
                        request = None

                # Convert to DataFrame
                comments_df = pd.DataFrame(comments_data)

                # Add video metadata
                comments_df["video_id"] = video_id
                comments_df["video_url"] = self.video_url

                # Sort columns for better organization
                column_order = [
                    "video_id",
                    "video_url",
                    "comment_id",
                    "parent_comment_id",
                    "is_reply",
                    "author",
                    "author_channel_url",
                    "text",
                    "published_at",
                    "updated_at",
                ]

                if self.include_metrics:
                    column_order.extend(["like_count", "reply_count"])

                comments_df = comments_df[column_order]

                return DataFrame(comments_df)

        except HttpError as e:
            error_message = f"YouTube API error: {e!s}"
            if e.resp.status == self.COMMENTS_DISABLED_STATUS:
                error_message = "Comments are disabled for this video or API quota exceeded."
            elif e.resp.status == self.NOT_FOUND_STATUS:
                error_message = "Video not found."

            return DataFrame(pd.DataFrame({"error": [error_message]}))