async def prepare_files(cls, media, session: StreamSession, headers=None) -> list:
        if headers is None:
            headers = {}
        files = []
        for index, (_file, file_name) in enumerate(media):

            data_bytes = to_bytes(_file)
            # Check Cache
            hasher = hashlib.md5()
            hasher.update(data_bytes)
            image_hash = hasher.hexdigest()
            file = ImagesCache.get(image_hash)
            if cls.image_cache and file:
                debug.log("Using cached image")
                files.append(file)
                continue

            extension, file_type = detect_file_type(data_bytes)
            file_name = file_name or f"file-{len(data_bytes)}{extension}"
            file_size = len(data_bytes)

            # Get File Url
            async with session.post(
                    f'{cls.url}/api/v2/files/getstsToken',
                    json={"filename": file_name,
                          "filesize": file_size, "filetype": file_type},
                    headers=headers

            ) as r:
                await raise_for_status(r, "Create file failed")
                res_data = await r.json()
                data = res_data.get("data")

                if res_data["success"] is False:
                    raise RateLimitError(f"{data['code']}:{data['details']}")
                file_url = data.get("file_url")
                file_id = data.get("file_id")

            # Put File into Url
            str_date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            headers = get_oss_headers('PUT', str_date, data, file_type)
            async with session.put(
                    file_url.split("?")[0],
                    data=data_bytes,
                    headers=headers
            ) as response:
                await raise_for_status(response)

            file_class: Literal["default", "vision", "video", "audio", "document"]
            _type: Literal["file", "image", "video", "audio"]
            show_type: Literal["file", "image", "video", "audio"]
            if "image" in file_type:
                _type = "image"
                show_type = "image"
                file_class = "vision"
            elif "video" in file_type:
                _type = "video"
                show_type = "video"
                file_class = "video"
            elif "audio" in file_type:
                _type = "audio"
                show_type = "audio"
                file_class = "audio"
            else:
                _type = "file"
                show_type = "file"
                file_class = "document"

            file = {
                "type": _type,
                "file": {
                    "created_at": int(time() * 1000),
                    "data": {},
                    "filename": file_name,
                    "hash": None,
                    "id": file_id,
                    "meta": {
                        "name": file_name,
                        "size": file_size,
                        "content_type": file_type
                    },
                    "update_at": int(time() * 1000),
                },
                "id": file_id,
                "url": file_url,
                "name": file_name,
                "collection_name": "",
                "progress": 0,
                "status": "uploaded",
                "greenNet": "success",
                "size": file_size,
                "error": "",
                "itemId": str(uuid.uuid4()),
                "file_type": file_type,
                "showType": show_type,
                "file_class": file_class,
                "uploadTaskId": str(uuid.uuid4())
            }
            debug.log(f"Uploading file: {file_url}")
            ImagesCache[image_hash] = file
            files.append(file)
        return files