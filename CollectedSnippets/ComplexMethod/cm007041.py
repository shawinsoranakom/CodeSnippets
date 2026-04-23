def get_trending_videos(self) -> DataFrame:
        """Retrieves trending videos from YouTube and returns as DataFrame."""
        try:
            # Validate max_results
            if not 1 <= self.max_results <= MAX_API_RESULTS:
                self.max_results = min(max(1, self.max_results), MAX_API_RESULTS)

            # Use context manager for YouTube API client
            with self.youtube_client() as youtube:
                # Get country code
                region_code = self.COUNTRY_CODES[self.region]

                # Prepare API request parts
                parts = ["snippet"]
                if self.include_statistics:
                    parts.append("statistics")
                if self.include_content_details:
                    parts.append("contentDetails")

                # Prepare API request parameters
                request_params = {
                    "part": ",".join(parts),
                    "chart": "mostPopular",
                    "regionCode": region_code,
                    "maxResults": self.max_results,
                }

                # Add category filter if not "All"
                if self.category != "All":
                    request_params["videoCategoryId"] = self.VIDEO_CATEGORIES[self.category]

                # Get trending videos
                request = youtube.videos().list(**request_params)
                response = request.execute()

                videos_data = []
                for item in response.get("items", []):
                    video_data = {
                        "video_id": item["id"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "channel_id": item["snippet"]["channelId"],
                        "channel_title": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                        "url": f"https://www.youtube.com/watch?v={item['id']}",
                        "region": self.region,
                        "category": self.category,
                    }

                    # Add thumbnails if requested
                    if self.include_thumbnails:
                        for size, thumb in item["snippet"]["thumbnails"].items():
                            video_data[f"thumbnail_{size}_url"] = thumb["url"]
                            video_data[f"thumbnail_{size}_width"] = thumb.get("width", 0)
                            video_data[f"thumbnail_{size}_height"] = thumb.get("height", 0)

                    # Add statistics if requested
                    if self.include_statistics and "statistics" in item:
                        video_data.update(
                            {
                                "view_count": int(item["statistics"].get("viewCount", 0)),
                                "like_count": int(item["statistics"].get("likeCount", 0)),
                                "comment_count": int(item["statistics"].get("commentCount", 0)),
                            }
                        )

                    # Add content details if requested
                    if self.include_content_details and "contentDetails" in item:
                        content_details = item["contentDetails"]
                        video_data.update(
                            {
                                "duration": self._format_duration(content_details["duration"]),
                                "definition": content_details.get("definition", "hd").upper(),
                                "has_captions": content_details.get("caption", "false") == "true",
                                "licensed_content": content_details.get("licensedContent", False),
                                "projection": content_details.get("projection", "rectangular"),
                            }
                        )

                    videos_data.append(video_data)

                # Convert to DataFrame
                videos_df = pd.DataFrame(videos_data)

                # Organize columns
                column_order = [
                    "video_id",
                    "title",
                    "channel_id",
                    "channel_title",
                    "category",
                    "region",
                    "published_at",
                    "url",
                    "description",
                ]

                if self.include_statistics:
                    column_order.extend(["view_count", "like_count", "comment_count"])

                if self.include_content_details:
                    column_order.extend(["duration", "definition", "has_captions", "licensed_content", "projection"])

                # Add thumbnail columns at the end if included
                if self.include_thumbnails:
                    thumbnail_cols = [col for col in videos_df.columns if col.startswith("thumbnail_")]
                    column_order.extend(sorted(thumbnail_cols))

                # Reorder columns, including any that might not be in column_order
                remaining_cols = [col for col in videos_df.columns if col not in column_order]
                videos_df = videos_df[column_order + remaining_cols]

                return DataFrame(videos_df)

        except HttpError as e:
            error_message = f"YouTube API error: {e}"
            if e.resp.status == HTTP_FORBIDDEN:
                error_message = "API quota exceeded or access forbidden."
            elif e.resp.status == HTTP_NOT_FOUND:
                error_message = "Resource not found."

            return DataFrame(pd.DataFrame({"error": [error_message]}))

        except Exception as e:  # noqa: BLE001
            logger.exception("An unexpected error occurred:")
            return DataFrame(pd.DataFrame({"error": [str(e)]}))