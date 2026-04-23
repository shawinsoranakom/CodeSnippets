def test__crop_source_faces(self,
                                columns: int,
                                face_size: int,
                                monkeypatch: pytest.MonkeyPatch,
                                mocker: pytest_mock.MockerFixture) -> None:
        """ Test :class:`~tools.preview.viewer.FacesDisplay` _crop_source_faces method

        Parameters
        ----------
        columns: int
            The number of columns to display in the viewer
        face_size: int
            The size of each face image to be displayed in the viewer
        monkeypatch: :class:`pytest.MonkeyPatch`
            For patching the transform_image function
        mocker: :class:`pytest_mock.MockerFixture`
            Mocker for mocking various internal methods
        """
        f_display = self.get_faces_display_instance(columns, face_size)
        f_display._centering = "face"
        f_display.update_source = True

        transform_image_mock = mocker.MagicMock(return_value=np.zeros((face_size, face_size, 3),
                                                                      dtype=np.uint8))
        monkeypatch.setattr("tools.preview.viewer.transform_image", transform_image_mock)

        mats = np.random.random((columns, 2, 3)).astype(np.float32)
        f_display.source = [mocker.MagicMock() for _ in range(columns)]
        for idx, mock in enumerate(f_display.source):
            assert isinstance(mock, MagicMock)
            mock.inbound.detected_faces.__getitem__ = lambda self, x, y=mock: y
            mock.aligned.matrix = mats[idx]
            mock.inbound.filename = f"test_filename_{idx}.txt"

        f_display._crop_source_faces()

        assert len(f_display._faces.filenames) == columns
        assert len(f_display._faces.matrix) == columns
        assert len(f_display._faces.src) == columns
        assert not f_display.update_source
        assert transform_image_mock.call_count == columns

        for idx in range(columns):
            assert f_display._faces.filenames[idx] == f"test_filename_{idx}"
            assert np.all(f_display._faces.matrix[idx] == mats[idx])