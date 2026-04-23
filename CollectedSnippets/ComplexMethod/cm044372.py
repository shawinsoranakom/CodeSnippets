def test__handle_duplicate(self, faces_instance: Faces, mocker: pytest_mock.MockerFixture
                               ) -> None:
        """ Test for :class:`~tools.alignments.media.Faces` _handle_duplicate method

        Parameters
        ----------
        faces_instance: :class:`~tools.alignments.media.Faces`
            The class instance for testing
        """
        faces = faces_instance
        dupe_dir = os.path.join(faces.folder, "_duplicates")
        src_filename = "test_0001.png"
        src_face_idx = 0
        paths = [os.path.join(faces.folder, fname) for fname in os.listdir(faces.folder)]
        data = mocker.MagicMock()
        data.source.source_filename = src_filename
        data.source.face_index = src_face_idx
        seen: dict[str, list[int]] = {}

        # New item
        is_dupe = faces._handle_duplicate(paths[0], data, seen)  # type:ignore
        assert src_filename in seen and seen[src_filename] == [src_face_idx]
        assert not os.path.exists(dupe_dir)
        assert not is_dupe

        # Dupe item
        is_dupe = faces._handle_duplicate(paths[1], data, seen)  # type:ignore
        assert src_filename in seen and seen[src_filename] == [src_face_idx]
        assert len(seen) == 1
        assert os.path.exists(dupe_dir)
        assert not os.path.exists(paths[1])
        assert is_dupe

        # Move everything back for fixture cleanup
        os.rename(os.path.join(dupe_dir, os.path.basename(paths[1])), paths[1])
        os.rmdir(dupe_dir)