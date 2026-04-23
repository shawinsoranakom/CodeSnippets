def _build_item_response(
        self, source_dir_id: str, path: Path, is_child: bool = False
    ) -> BrowseMediaSource | None:
        mime_type, _ = mimetypes.guess_type(str(path))
        is_file = path.is_file()
        is_dir = path.is_dir()

        # Make sure it's a file or directory
        if not is_file and not is_dir:
            return None

        # Check that it's a media file
        if is_file and (
            not mime_type or mime_type.split("/")[0] not in MEDIA_MIME_TYPES
        ):
            return None

        title = path.name

        media_class = MediaClass.DIRECTORY
        if mime_type:
            media_class = MEDIA_CLASS_MAP.get(
                mime_type.split("/")[0], MediaClass.DIRECTORY
            )

        media = BrowseMediaSource(
            domain=self.domain,
            identifier=f"{source_dir_id}/{path.relative_to(self.media_dirs[source_dir_id])}",
            media_class=media_class,
            media_content_type=mime_type or "",
            title=title,
            can_play=is_file,
            can_expand=is_dir,
        )

        if is_file or is_child:
            return media

        # Append first level children
        media.children = []
        for child_path in path.iterdir():
            if child_path.name[0] != ".":
                child = self._build_item_response(source_dir_id, child_path, True)
                if child:
                    media.children.append(child)

        # Sort children showing directories first, then by name
        media.children.sort(key=lambda child: (child.can_play, child.title))

        return media