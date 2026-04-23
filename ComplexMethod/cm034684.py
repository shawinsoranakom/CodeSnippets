async def prepare_images(cls, args, media: list[tuple]) -> list[dict[str, str]]:
        files = []
        if not media:
            return files
        async with StreamSession(**args, ) as session:
            for index, (_file, file_name) in enumerate(media):
                data_bytes = to_bytes(_file)
                # Check Cache
                hasher = hashlib.md5()
                hasher.update(data_bytes)
                image_hash = hasher.hexdigest()
                file = ImagesCache.get(image_hash)
                if cls.image_cache and file:
                    if check_link_expiry(file.get("url")):
                        debug.log("Using cached image")
                        files.append(file)
                        continue
                    debug.log("Expiry cached image")

                extension, file_type = detect_file_type(data_bytes)
                file_name = file_name or f"file-{len(data_bytes)}{extension}"
                async with session.post(
                        url=cls.url,
                        json=[file_name, file_type],
                        headers={
                            "accept": "text/x-component",
                            "content-type": "text/plain;charset=UTF-8",
                            "next-action": cls._next_actions["generateUploadUrl"],
                            "referer": cls.url
                        }
                ) as response:
                    await raise_for_status(response)
                    text = await response.text()
                    line = next(filter(lambda x: x.startswith("1:"), text.split("\n")), "")
                    if not line:
                        raise Exception("Failed to get upload URL")
                    chunk = json.loads(line[2:])
                    if not chunk.get("success"):
                        raise Exception("Failed to get upload URL")
                    uploadUrl = chunk.get("data", {}).get("uploadUrl")
                    key = chunk.get("data", {}).get("key")
                    if not uploadUrl:
                        raise Exception("Failed to get upload URL")

                async with session.put(
                    url=uploadUrl,
                    headers={
                        "content-type": file_type,
                    },
                    data=data_bytes,
                ) as response:
                    await raise_for_status(response)
                async with session.post(
                        url=cls.url,
                        json=[key],
                        headers={
                            "accept": "text/x-component",
                            "content-type": "text/plain;charset=UTF-8",
                            "next-action": cls._next_actions["getSignedUrl"],
                            "referer": cls.url
                        }
                ) as response:
                    await raise_for_status(response)
                    text = await response.text()
                    line = next(filter(lambda x: x.startswith("1:"), text.split("\n")), "")
                    if not line:
                        raise Exception("Failed to get download URL")

                    chunk = json.loads(line[2:])
                    if not chunk.get("success"):
                        raise Exception("Failed to get download URL")
                    image_url = chunk.get("data", {}).get("url")
                    uploaded_file = {
                        "name": key,
                        "contentType": file_type,
                        "url": image_url
                    }
                debug.log(f"Uploaded image to: {image_url}")
                ImagesCache[image_hash] = uploaded_file
                files.append(uploaded_file)
        return files