def test_init(self) -> None:
        """ Test :class:`~tools.preview.viewer.FacesDisplay` __init__ method """
        f_display = self.get_faces_display_instance(face_size=256)
        assert f_display._size == 256
        assert f_display._padding == self._padding
        assert isinstance(f_display._app, MagicMock)

        assert f_display._display_dims == (1, 1)
        assert isinstance(f_display._faces, _Faces)

        assert f_display._centering is None
        assert f_display._faces_source.size == 0
        assert f_display._faces_dest.size == 0
        assert f_display._tk_image is None
        assert f_display.update_source is False
        assert not f_display.source and isinstance(f_display.source, list)
        assert not f_display.destination and isinstance(f_display.destination, list)