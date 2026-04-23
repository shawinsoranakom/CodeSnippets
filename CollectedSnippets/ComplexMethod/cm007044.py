def get_channel_info(self) -> DataFrame:
        """Retrieves channel information and returns it as a DataFrame."""
        youtube = None
        try:
            # Get channel ID and initialize YouTube API client
            channel_id = self._extract_channel_id(self.channel_url)
            youtube = build("youtube", "v3", developerKey=self.api_key)

            # Prepare parts for the API request
            parts = ["snippet", "contentDetails"]
            if self.include_statistics:
                parts.append("statistics")
            if self.include_branding:
                parts.append("brandingSettings")

            # Get channel information
            channel_response = youtube.channels().list(part=",".join(parts), id=channel_id).execute()

            if not channel_response["items"]:
                return DataFrame(pd.DataFrame({"error": ["Channel not found"]}))

            channel_info = channel_response["items"][0]

            # Build basic channel data
            channel_data = {
                "title": [channel_info["snippet"]["title"]],
                "description": [channel_info["snippet"]["description"]],
                "custom_url": [channel_info["snippet"].get("customUrl", "")],
                "published_at": [channel_info["snippet"]["publishedAt"]],
                "country": [channel_info["snippet"].get("country", "Not specified")],
                "channel_id": [channel_id],
            }

            # Add thumbnails
            for size, thumb in channel_info["snippet"]["thumbnails"].items():
                channel_data[f"thumbnail_{size}"] = [thumb["url"]]

            # Add statistics if requested
            if self.include_statistics:
                stats = channel_info["statistics"]
                channel_data.update(
                    {
                        "view_count": [int(stats.get("viewCount", 0))],
                        "subscriber_count": [int(stats.get("subscriberCount", 0))],
                        "hidden_subscriber_count": [stats.get("hiddenSubscriberCount", False)],
                        "video_count": [int(stats.get("videoCount", 0))],
                    }
                )

            # Add branding if requested
            if self.include_branding:
                branding = channel_info.get("brandingSettings", {})
                channel_data.update(
                    {
                        "brand_title": [branding.get("channel", {}).get("title", "")],
                        "brand_description": [branding.get("channel", {}).get("description", "")],
                        "brand_keywords": [branding.get("channel", {}).get("keywords", "")],
                        "brand_banner_url": [branding.get("image", {}).get("bannerExternalUrl", "")],
                    }
                )

            # Create the initial DataFrame
            channel_df = pd.DataFrame(channel_data)

            # Add playlists if requested
            if self.include_playlists:
                playlists = self._get_channel_playlists(youtube, channel_id)
                if playlists and "error" not in playlists[0]:
                    # Create a DataFrame for playlists
                    playlists_df = pd.DataFrame(playlists)
                    # Join with main DataFrame
                    channel_df = pd.concat([channel_df] * len(playlists_df), ignore_index=True)
                    for column in playlists_df.columns:
                        channel_df[column] = playlists_df[column].to_numpy()

            return DataFrame(channel_df)

        except (HttpError, HTTPError) as e:
            return DataFrame(pd.DataFrame({"error": [str(e)]}))
        finally:
            if youtube:
                youtube.close()