async def copy_image(image: str, target: str = None) -> str:
            """Process individual image and return its local URL"""
            # Skip if image is already local
            if image is None or image.startswith("/"):
                return image
            target_path = target
            media_extension = ""
            if target_path is None:
                # Build safe filename with full Unicode support
                media_extension = get_media_extension(image)
                path = urlparse(image).path
                if path.startswith("/media/"):
                    filename = secure_filename(path[len("/media/"):])
                else:
                    filename = get_filename(tags, alt, media_extension, image)
                target_path = os.path.join(media_dir, filename)
            try:
                # Handle different image types
                if image.startswith("data:"):
                    with open(target_path, "wb") as f:
                        f.write(extract_data_uri(image))
                elif not os.path.exists(target_path) or os.lstat(target_path).st_size <= 0:
                    if not is_safe_url(image):
                        raise ValueError("Invalid or disallowed media URL")
                    # Use aiohttp to fetch the image
                    async with session.get(image, ssl=ssl) as response:
                        response.raise_for_status()
                        if target is None:
                            filename = update_filename(response, filename)
                            target_path = os.path.join(media_dir, filename)
                        media_type = response.headers.get("content-type", "application/octet-stream")
                        if media_type not in ("application/octet-stream", "binary/octet-stream"):
                            if media_type not in MEDIA_TYPE_MAP:
                                raise ValueError(f"Unsupported media type: {media_type}")
                            if target is None and not media_extension:
                                media_extension = f".{MEDIA_TYPE_MAP[media_type]}"
                                target_path = f"{target_path}{media_extension}"
                        with open(target_path, "wb") as f:
                            async for chunk in response.content.iter_any():
                                f.write(chunk)
                # Verify file format
                if target is None and not media_extension:
                    with open(target_path, "rb") as f:
                        file_header = f.read(12)
                    try:
                        detected_type = is_accepted_format(file_header)
                        media_extension = f".{detected_type.split('/')[-1]}"
                        media_extension = media_extension.replace("jpeg", "jpg")
                        os.rename(target_path, f"{target_path}{media_extension}")
                        target_path = f"{target_path}{media_extension}"
                    except ValueError:
                        pass
                if thumbnail:
                    uri = "/thumbnail/" + os.path.basename(target_path)
                else:
                    uri = f"/media/{os.path.basename(target_path)}" + ('?' + (add_url if isinstance(add_url, str) else '' + 'url=' + quote(image)) if add_url and not image.startswith('data:') else '')
                if return_target:
                    return uri, target_path
                return uri

            except (ClientError, IOError, OSError, ValueError) as e:
                debug.error(f"Image copying failed:", e)
                if target_path and os.path.exists(target_path):
                    os.unlink(target_path)
                return image