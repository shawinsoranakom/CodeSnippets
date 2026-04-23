async def stream_audio(filename: str, request: Request):
    audio_path = os.path.join("podcasts/audio", filename)
    if not os.path.exists(audio_path):
        return Response(status_code=404, content="Audio file not found")
    file_size = os.path.getsize(audio_path)
    range_header = request.headers.get("Range", "").strip()
    start = 0
    end = file_size - 1
    if range_header:
        try:
            range_data = range_header.replace("bytes=", "").split("-")
            start = int(range_data[0]) if range_data[0] else 0
            end = int(range_data[1]) if len(range_data) > 1 and range_data[1] else file_size - 1
        except ValueError:
            return Response(status_code=400, content="Invalid range header")
    end = min(end, file_size - 1)
    content_length = end - start + 1
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
        "Content-Disposition": f"inline; filename={filename}",
        "Content-Type": "audio/wav",
    }

    async def file_streamer():
        async with aiofiles.open(audio_path, "rb") as f:
            await f.seek(start)
            remaining = content_length
            chunk_size = 64 * 1024
            while remaining > 0:
                chunk = await f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    status_code = 206 if range_header else 200
    return StreamingResponse(file_streamer(), status_code=status_code, headers=headers)