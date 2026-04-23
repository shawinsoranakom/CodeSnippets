def test_valid_extension(self, media_loader_instance: MediaLoader) -> None:
        """ Test for :class:`~tools.alignments.media.MediaLoader` valid_extension method

        Parameters
        ----------
        media_loader_instance: :class:`~tools.alignments.media.MediaLoader`
            The class instance for testing
        """
        media_loader = media_loader_instance
        assert media_loader.valid_extension("test.png")
        assert media_loader.valid_extension("test.PNG")
        assert media_loader.valid_extension("test.jpg")
        assert media_loader.valid_extension("test.JPG")
        assert not media_loader.valid_extension("test.doc")
        assert not media_loader.valid_extension("test.txt")
        assert not media_loader.valid_extension("test.mp4")