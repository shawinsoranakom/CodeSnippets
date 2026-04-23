async def get(
        self, request: web.Request, device_id: str, filename: str
    ) -> web.StreamResponse:
        """Start a get request."""
        device_conversions = self.proxy_data.conversions[device_id]
        if not device_conversions:
            return web.Response(
                body="No proxy URL for device", status=HTTPStatus.NOT_FOUND
            )

        # {id}.mp3 -> id, mp3
        convert_id, media_format = filename.rsplit(".")

        # Look up conversion info
        convert_info: FFmpegConversionInfo | None = None
        for maybe_convert_info in device_conversions:
            if (maybe_convert_info.convert_id == convert_id) and (
                maybe_convert_info.media_format == media_format
            ):
                convert_info = maybe_convert_info
                break

        if convert_info is None:
            return web.Response(body="Invalid proxy URL", status=HTTPStatus.BAD_REQUEST)

        # Stop previous process if the URL is being reused.
        # We could continue from where the previous connection left off, but
        # there would be no media header.
        if (convert_info.proc is not None) and (convert_info.proc.returncode is None):
            convert_info.proc.kill()
            convert_info.proc = None

        # Stream converted audio back to client
        resp = FFmpegConvertResponse(
            self.manager, convert_info, device_id, self.proxy_data
        )
        writer = await resp.prepare(request)
        assert writer is not None
        await resp.transcode(request, writer)
        return resp