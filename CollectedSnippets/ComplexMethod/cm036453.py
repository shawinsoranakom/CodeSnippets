async def test_fetch_image_base64(
    url_images: dict[str, Image.Image], raw_image_url: str, suffix: str
):
    connector = MediaConnector(
        # Domain restriction should not apply to data URLs.
        allowed_media_domains=[
            "www.bogotobogo.com",
            "github.com",
        ]
    )
    url_image = url_images[raw_image_url]

    try:
        mime_type = Image.MIME[Image.registered_extensions()[suffix]]
    except KeyError:
        try:
            mime_type = mimetypes.types_map[suffix]
        except KeyError:
            pytest.skip("No MIME type")

    with NamedTemporaryFile(suffix=suffix) as f:
        try:
            url_image.save(f.name)
        except Exception as e:
            if e.args[0] == "cannot write mode RGBA as JPEG":
                pytest.skip("Conversion not supported")

            raise

        base64_image = base64.b64encode(f.read()).decode("utf-8")
        data_url = f"data:{mime_type};base64,{base64_image}"

        data_image_sync = connector.fetch_image(data_url)
        if _image_equals(url_image, Image.open(f)):
            assert _image_equals(url_image, data_image_sync)
        else:
            pass  # Lossy format; only check that image can be opened

        data_image_async = await connector.fetch_image_async(data_url)
        assert _image_equals(data_image_sync, data_image_async)