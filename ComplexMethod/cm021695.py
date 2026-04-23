def __init__(self, media_types: list[str]) -> None:
        """Initialize mock search results."""
        self.artists = []
        self.albums = []
        self.tracks = []
        self.playlists = []
        self.radio = []
        self.podcasts = []
        self.audiobooks = []

        # Create mock items based on requested media types
        for media_type in media_types:
            items = []
            for i in range(5):  # Create 5 mock items for each type
                item = MagicMock()
                item.name = f"Test {media_type} {i}"
                item.uri = f"library://{media_type}/{i}"
                item.available = True
                item.artists = []
                media_type_mock = MagicMock()
                media_type_mock.value = media_type
                item.media_type = media_type_mock
                items.append(item)

            # Assign to the appropriate attribute
            if media_type == "artist":
                self.artists = items
            elif media_type == "album":
                self.albums = items
            elif media_type == "track":
                self.tracks = items
            elif media_type == "playlist":
                self.playlists = items
            elif media_type == "radio":
                self.radio = items
            elif media_type == "podcast":
                self.podcasts = items
            elif media_type == "audiobook":
                self.audiobooks = items