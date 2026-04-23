def image_upload(post, image_save_function=None):
            image = post.get("image")
            overwrite = post.get("overwrite")
            image_is_duplicate = False

            image_upload_type = post.get("type")
            upload_dir, image_upload_type = get_dir_by_type(image_upload_type)

            if image and image.file:
                filename = image.filename
                if not filename:
                    return web.Response(status=400)

                subfolder = post.get("subfolder", "")
                full_output_folder = os.path.join(upload_dir, os.path.normpath(subfolder))
                filepath = os.path.abspath(os.path.join(full_output_folder, filename))

                if os.path.commonpath((upload_dir, filepath)) != upload_dir:
                    return web.Response(status=400)

                if not os.path.exists(full_output_folder):
                    os.makedirs(full_output_folder)

                split = os.path.splitext(filename)

                if overwrite is not None and (overwrite == "true" or overwrite == "1"):
                    pass
                else:
                    i = 1
                    while os.path.exists(filepath):
                        if compare_image_hash(filepath, image): #compare hash to prevent saving of duplicates with same name, fix for #3465
                            image_is_duplicate = True
                            break
                        filename = f"{split[0]} ({i}){split[1]}"
                        filepath = os.path.join(full_output_folder, filename)
                        i += 1

                if not image_is_duplicate:
                    if image_save_function is not None:
                        image_save_function(image, post, filepath)
                    else:
                        with open(filepath, "wb") as f:
                            f.write(image.file.read())

                resp = {"name" : filename, "subfolder": subfolder, "type": image_upload_type}

                if args.enable_assets:
                    try:
                        tag = image_upload_type if image_upload_type in ("input", "output") else "input"
                        result = register_file_in_place(abs_path=filepath, name=filename, tags=[tag])
                        resp["asset"] = {
                            "id": result.ref.id,
                            "name": result.ref.name,
                            "asset_hash": result.asset.hash,
                            "size": result.asset.size_bytes,
                            "mime_type": result.asset.mime_type,
                            "tags": result.tags,
                        }
                    except Exception:
                        logging.warning("Failed to register uploaded image as asset", exc_info=True)

                return web.json_response(resp)
            else:
                return web.Response(status=400)