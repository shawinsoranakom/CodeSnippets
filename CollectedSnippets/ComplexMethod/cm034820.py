def upload_files(bucket_id: str):
            bucket_id = secure_filename(bucket_id)
            bucket_dir = get_bucket_dir(bucket_id)
            media_dir = os.path.join(bucket_dir, "media")
            os.makedirs(bucket_dir, exist_ok=True)
            filenames = []
            media = []
            for file in request.files.getlist('files'):
                filename = secure_filename(file.filename)
                mimetype = file.mimetype.split(";")[0]
                if (not filename or filename == "blob") and mimetype in MEDIA_TYPE_MAP:
                    filename = f"file.{MEDIA_TYPE_MAP[mimetype]}"
                suffix = os.path.splitext(filename)[1].lower()
                copyfile = get_tempfile(file, suffix)
                result = None
                if has_markitdown and not filename.endswith((".md", ".json", ".zip")):
                    try:
                        language = request.headers.get("x-recognition-language")
                        md = MarkItDown()
                        result = md.convert(copyfile, stream_info=StreamInfo(
                            extension=suffix,
                            mimetype=file.mimetype,
                        ), recognition_language=language).text_content
                    except Exception as e:
                        logger.exception(e)
                is_media = is_allowed_extension(filename)
                is_supported = result or supports_filename(filename)
                if not is_media and not is_supported:
                    os.remove(copyfile)
                    continue
                if not is_media and result:
                    with open(os.path.join(bucket_dir, f"{filename}.md"), 'w', encoding="utf-8") as f:
                        f.write(f"{result}\n")
                    filenames.append(f"{filename}.md")
                if is_media:
                    os.makedirs(media_dir, exist_ok=True)
                    newfile = os.path.join(media_dir, filename)
                    image_size = {}
                    if has_pillow:
                        try:
                            image = Image.open(copyfile)
                            width, height = image.size
                            image_size = {"width": width, "height": height}
                            thumbnail_dir = os.path.join(bucket_dir, "thumbnail")
                            os.makedirs(thumbnail_dir, exist_ok=True)
                            width, height = process_image(image, save=os.path.join(thumbnail_dir, filename))
                            image_size = {"width": width, "height": height}
                        except UnidentifiedImageError:
                            pass
                        except Exception as e:
                            logger.exception(e)
                    if result:
                        media.append({"name": filename, "text": result, **image_size})
                    else:
                        media.append({"name": filename, **image_size})
                elif is_supported and not result:
                    newfile = os.path.join(bucket_dir, filename)
                    filenames.append(filename)
                else:
                    os.remove(copyfile)
                    if not result:
                        raise ValueError(f"Unsupported file type: {filename}")
                    continue
                try:
                    os.rename(copyfile, newfile)
                except OSError:
                    shutil.copyfile(copyfile, newfile)
                    os.remove(copyfile)
            with open(os.path.join(bucket_dir, "files.txt"), 'w', encoding="utf-8") as f:
                for filename in filenames:
                    f.write(f"{filename}\n")
            return {"bucket_id": bucket_id, "files": filenames, "media": media}