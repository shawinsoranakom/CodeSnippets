def media_image_url(self, item: Item) -> str | None:  # noqa: PLR0206
        """Return the media image URL."""
        if item.type == ItemType.EPISODE:
            if TYPE_CHECKING:
                assert isinstance(item, Episode)
            if item.images:
                return item.images[0].url
            if item.show and item.show.images:
                return item.show.images[0].url
            return None
        if TYPE_CHECKING:
            assert isinstance(item, Track)
        if not item.album.images:
            return None
        return item.album.images[0].url