async def handle_media(request: web.Request) -> web.Response:
            """Serve media files from generated_media directory"""
            filename = request.match_info.get('filename', '')
            if not filename:
                return web.Response(status=404, text="File not found")

            def get_timestamp(s):
                m = re.match("^[0-9]+", s)
                return int(m.group(0)) if m else 0

            target = os.path.join(get_media_dir(), os.path.basename(filename))

            # Try URL-decoded filename if not found
            if not os.path.isfile(target):
                other_name = os.path.join(get_media_dir(), os.path.basename(unquote_plus(filename)))
                if os.path.isfile(other_name):
                    target = other_name

            # Get file extension and mime type
            ext = os.path.splitext(filename)[1][1:].lower()
            mime_type = EXTENSIONS_MAP.get(ext, "application/octet-stream")

            # Try to fetch from backend if file doesn't exist
            if not os.path.isfile(target) and mime_type != "application/octet-stream":
                source_url = get_source_url(str(request.query_string))
                ssl = None
                if source_url is not None:
                    try:
                        await copy_media([source_url], target=target, ssl=ssl)
                        sys.stderr.write(f"File copied from {source_url}\n")
                    except Exception as e:
                        sys.stderr.write(f"Download failed: {source_url} - {e}\n")
                        raise web.HTTPFound(location=source_url)

            if not os.path.isfile(target):
                return web.Response(status=404, text="File not found")

            # Build response headers
            stat_result = os.stat(target)
            headers = {
                "cache-control": "public, max-age=31536000",
                "last-modified": formatdate(get_timestamp(filename), usegmt=True),
                "etag": f'"{hashlib.md5(filename.encode()).hexdigest()}"',
                "content-length": str(stat_result.st_size),
                "content-type": mime_type,
                "access-control-allow-origin": "*",
            }

            # Check for conditional request
            if_none_match = request.headers.get("if-none-match")
            if if_none_match:
                etag = headers["etag"]
                if etag in [tag.strip(" W/") for tag in if_none_match.split(",")]:
                    return web.Response(status=304, headers=headers)

            # Serve the file
            return web.FileResponse(target, headers=headers)