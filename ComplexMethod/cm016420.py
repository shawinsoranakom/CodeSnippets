async def test_listuserdata_normalized_separator(aiohttp_client, app, tmp_path):
    os_sep = "\\"
    with patch("os.sep", os_sep):
        with patch("os.path.sep", os_sep):
            os.makedirs(tmp_path / "test_dir" / "subdir")
            with open(tmp_path / "test_dir" / "subdir" / "file1.txt", "w") as f:
                f.write("test content")

            client = await aiohttp_client(app)
            resp = await client.get("/userdata?dir=test_dir&recurse=true")
            assert resp.status == 200
            result = await resp.json()
            assert len(result) == 1
            assert "/" in result[0]  # Ensure forward slash is used
            assert "\\" not in result[0]  # Ensure backslash is not present
            assert result[0] == "subdir/file1.txt"

            # Test with full_info
            resp = await client.get(
                "/userdata?dir=test_dir&recurse=true&full_info=true"
            )
            assert resp.status == 200
            result = await resp.json()
            assert len(result) == 1
            assert "/" in result[0]["path"]  # Ensure forward slash is used
            assert "\\" not in result[0]["path"]  # Ensure backslash is not present
            assert result[0]["path"] == "subdir/file1.txt"