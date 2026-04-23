async def get_media(filename, request: Request, thumbnail: bool = False):
            def get_timestamp(str):
                m=re.match("^[0-9]+", str)
                if m:
                    return int(m.group(0))
                else:
                    return 0
            target = os.path.join(get_media_dir(), os.path.basename(filename))
            if thumbnail and has_pillow:
                thumbnail_dir = os.path.join(get_media_dir(), "thumbnails")
                thumbnail = os.path.join(thumbnail_dir, filename)
            if not os.path.isfile(target):
                other_name = os.path.join(get_media_dir(), os.path.basename(quote_plus(filename)))
                if os.path.isfile(other_name):
                    target = other_name
            ext = os.path.splitext(filename)[1][1:]
            mime_type = EXTENSIONS_MAP.get(ext)
            stat_result = SimpleNamespace()
            stat_result.st_size = 0
            stat_result.st_mtime = get_timestamp(filename)
            if thumbnail and has_pillow and os.path.isfile(thumbnail):
                stat_result.st_size = os.stat(thumbnail).st_size
            elif not thumbnail and os.path.isfile(target):
                stat_result.st_size = os.stat(target).st_size
            headers = {
                "cache-control": "public, max-age=31536000",
                "last-modified": formatdate(stat_result.st_mtime, usegmt=True),
                "etag": f'"{hashlib.md5(filename.encode()).hexdigest()}"',
                **({
                    "content-length": str(stat_result.st_size),
                } if stat_result.st_size else {}),
                **({} if thumbnail or mime_type is None else {
                    "content-type": mime_type,
                })
            }
            response = FileResponse(
                target,
                headers=headers,
                filename=filename,
            )
            try:
                if_none_match = request.headers["if-none-match"]
                etag = response.headers["etag"]
                if etag in [tag.strip(" W/") for tag in if_none_match.split(",")]:
                    return NotModifiedResponse(response.headers)
            except KeyError:
                pass
            if not os.path.isfile(target) and mime_type is not None:
                source_url = get_source_url(str(request.query_params))
                ssl = None
                if source_url is None:
                    backend_url = os.environ.get("G4F_BACKEND_URL")
                    if backend_url:
                        source_url = f"{backend_url}/media/{filename}"
                        ssl = False
                if source_url is not None:
                    try:
                        await copy_media(
                            [source_url],
                            target=target, ssl=ssl)
                        debug.log(f"File copied from {source_url}")
                    except Exception as e:
                        debug.error(f"Download failed:  {source_url}")
                        debug.error(e)
                        return RedirectResponse(url=source_url)
            if thumbnail and has_pillow:
                try:
                    if not os.path.isfile(thumbnail):
                        image = Image.open(target)
                        os.makedirs(thumbnail_dir, exist_ok=True)
                        process_image(image, save=thumbnail)
                        debug.log(f"Thumbnail created: {thumbnail}")
                except Exception as e:
                    logger.exception(e)
            if thumbnail and os.path.isfile(thumbnail):
                result = thumbnail
            else:
                result = target
            if not os.path.isfile(result):
                return ErrorResponse.from_message("File not found", HTTP_404_NOT_FOUND)
            async def stream():
                with open(result, "rb") as file:
                    while True:
                        chunk = file.read(65536)
                        if not chunk:
                            break
                        yield chunk
            return StreamingResponse(stream(), headers=headers)