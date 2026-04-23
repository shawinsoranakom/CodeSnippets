def test_process_folder(self,
                            faces_instance: Faces,
                            mocker: pytest_mock.MockerFixture,
                            monkeypatch: pytest.MonkeyPatch) -> None:
        """ Test for :class:`~tools.alignments.media.Faces` process_folder method

        Parameters
        ----------
        faces_instance: :class:`~tools.alignments.media.Faces`
            The class instance for testing
        mocker: :class:`pytest_mock.MockerFixture`
            Fixture for mocking various logic calls
        """
        faces = faces_instance
        read_image_meta_mock = mocker.patch("tools.alignments.media.read_image_meta_batch")
        img_sources = [os.path.join(faces.folder, fname) for fname in os.listdir(faces.folder)]

        meta_data = {"itxt": {"source": ({"source_filename": "data.png",
                                          "alignments_version": 2.5,
                                          "face_index": 0,
                                          "original_filename": "data.png",
                                          "source_is_video": False,
                                          "source_frame_dims": (1280, 720)}),
                              "alignments": {"x": 1, "y": 2, "w": 3, "h": 4,
                                             "landmarks_xy": [[0.0, 1.1], [1.1, 2.2]]}}}
        png_mock = mocker.MagicMock()
        png_mock.source.source_filename = "data.png"
        monkeypatch.setattr("tools.alignments.media.PNGHeader.from_dict", lambda x: png_mock)

        expected = [(fname, png_mock) for fname in os.listdir(faces.folder)]
        read_image_meta_mock.side_effect = [[(src, meta_data) for src in img_sources]]

        dupe_mock = mocker.patch("tools.alignments.media.Faces._handle_duplicate",
                                 return_value=False)

        # valid itxt
        output = list(faces.process_folder())
        assert read_image_meta_mock.call_count == 1
        assert dupe_mock.call_count == 2
        assert output == expected

        dupe_mock.reset_mock()
        read_image_meta_mock.reset_mock()

        # valid itxt with alignments data
        read_image_meta_mock.side_effect = [[(src, meta_data) for src in img_sources]]
        faces._alignments = mocker.MagicMock(AlignmentData)
        faces._alignments.version = 2.1  # type:ignore
        output = list(faces.process_folder())
        assert faces._alignments.frame_exists.call_count == 2  # type:ignore
        assert read_image_meta_mock.call_count == 1
        assert dupe_mock.call_count == 2

        dupe_mock.reset_mock()
        read_image_meta_mock.reset_mock()
        faces._alignments = None

        # invalid itxt
        read_image_meta_mock.side_effect = [[(src, {}) for src in img_sources]]
        output = list(faces.process_folder())
        assert read_image_meta_mock.call_count == 1
        assert dupe_mock.call_count == 0
        assert not output