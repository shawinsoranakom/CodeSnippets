def _browse_media(
        self, source_dir_id: str | None, location: str
    ) -> BrowseMediaSource:
        """Browse media."""

        # If only one media dir is configured, use that as the local media root
        if source_dir_id is None and len(self.media_dirs) == 1:
            source_dir_id = list(self.media_dirs)[0]

        # Multiple folder, root is requested
        if source_dir_id is None:
            if location:
                raise BrowseError("Folder not found.")

            base = BrowseMediaSource(
                domain=self.domain,
                identifier="",
                media_class=MediaClass.DIRECTORY,
                media_content_type=None,
                title=self.name,
                can_play=False,
                can_expand=True,
                children_media_class=MediaClass.DIRECTORY,
            )

            base.children = [
                self._browse_media(source_dir_id, "")
                for source_dir_id in self.media_dirs
            ]

            return base

        full_path = Path(self.media_dirs[source_dir_id], location)

        if not full_path.exists():
            if location == "":
                raise BrowseError("Media directory does not exist.")
            raise BrowseError("Path does not exist.")

        if not full_path.is_dir():
            raise BrowseError("Path is not a directory.")

        result = self._build_item_response(source_dir_id, full_path)
        if not result:
            raise BrowseError("Unknown source directory.")
        return result