def test_get_model__write_zipfile(mocker: pytest_mock.MockerFixture,
                                  get_model_instance: GetModel,
                                  dl_type: str) -> None:
    """ Test :func:`~lib.utils.GetModel._write_zipfile` executes its logic correctly """
    response = mocker.MagicMock()
    assert not os.path.isfile(get_model_instance._model_zip_path)

    downloaded = 10 if dl_type == "complete" else 0
    response.getheader.return_value = 0

    if dl_type in ("new", "continue"):
        chunks = [32, 64, 128, 256, 512, 1024]
        data = [b"\x00" * size for size in chunks] + [b""]
        response.getheader.return_value = sum(chunks)
        response.read.side_effect = data

    if dl_type == "continue":  # Write a partial download of the correct size
        with open(get_model_instance._model_zip_path, "wb") as partial:
            partial.write(b"\x00" * sum(chunks))  # type:ignore
        downloaded = os.path.getsize(get_model_instance._model_zip_path)

    get_model_instance._write_zipfile(response, downloaded)

    if dl_type == "complete":  # Already downloaded. No more tests
        assert not response.read.called
        return

    assert response.read.call_count == len(data)  # all data read  # type:ignore
    assert os.path.isfile(get_model_instance._model_zip_path)
    downloaded_size = os.path.getsize(get_model_instance._model_zip_path)
    downloaded_size = downloaded_size if dl_type == "new" else downloaded_size // 2
    assert downloaded_size == sum(chunks)