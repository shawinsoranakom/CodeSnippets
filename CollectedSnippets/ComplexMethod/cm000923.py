async def test_image_embedded_as_vision_block(self, tmp_path):
        """JPEG images should become vision content blocks, not files on disk."""
        raw = b"\xff\xd8\xff\xe0fake-jpeg"
        info = _FakeFileInfo(
            id="abc",
            name="photo.jpg",
            path="/photo.jpg",
            mime_type="image/jpeg",
            size_bytes=len(raw),
        )
        mgr = AsyncMock()
        mgr.get_file_info.return_value = info
        mgr.read_file_by_id.return_value = raw

        with patch(_PATCH_TARGET, new_callable=AsyncMock, return_value=mgr):
            result = await _prepare_file_attachments(
                ["abc"], "user1", "sess1", str(tmp_path)
            )

        assert "1 file" in result.hint
        assert "photo.jpg" in result.hint
        assert "embedded as image" in result.hint
        assert len(result.image_blocks) == 1
        block = result.image_blocks[0]
        assert block["type"] == "image"
        assert block["source"]["media_type"] == "image/jpeg"
        assert block["source"]["data"] == base64.b64encode(raw).decode("ascii")
        # Image should NOT be written to disk (embedded instead)
        assert not os.path.exists(os.path.join(tmp_path, "photo.jpg"))