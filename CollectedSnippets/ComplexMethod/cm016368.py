async def view_image(request):
            if "filename" in request.rel_url.query:
                filename = request.rel_url.query["filename"]

                # The frontend's LoadImage combo widget uses asset_hash values
                # (e.g. "blake3:...") as widget values. When litegraph renders the
                # node preview, it constructs /view?filename=<asset_hash>, so this
                # endpoint must resolve blake3 hashes to their on-disk file paths.
                if filename.startswith("blake3:"):
                    owner_id = self.user_manager.get_request_user_id(request)
                    result = resolve_hash_to_path(filename, owner_id=owner_id)
                    if result is None:
                        return web.Response(status=404)
                    file, filename, resolved_content_type = result.abs_path, result.download_name, result.content_type
                else:
                    resolved_content_type = None
                    filename, output_dir = folder_paths.annotated_filepath(filename)

                    if not filename:
                        return web.Response(status=400)

                    # validation for security: prevent accessing arbitrary path
                    if filename[0] == '/' or '..' in filename:
                        return web.Response(status=400)

                    if output_dir is None:
                        type = request.rel_url.query.get("type", "output")
                        output_dir = folder_paths.get_directory_by_type(type)

                    if output_dir is None:
                        return web.Response(status=400)

                    if "subfolder" in request.rel_url.query:
                        full_output_dir = os.path.join(output_dir, request.rel_url.query["subfolder"])
                        if os.path.commonpath((os.path.abspath(full_output_dir), output_dir)) != output_dir:
                            return web.Response(status=403)
                        output_dir = full_output_dir

                    filename = os.path.basename(filename)
                    file = os.path.join(output_dir, filename)

                if os.path.isfile(file):
                    if 'preview' in request.rel_url.query:
                        with Image.open(file) as img:
                            preview_info = request.rel_url.query['preview'].split(';')
                            image_format = preview_info[0]
                            if image_format not in ['webp', 'jpeg'] or 'a' in request.rel_url.query.get('channel', ''):
                                image_format = 'webp'

                            quality = 90
                            if preview_info[-1].isdigit():
                                quality = int(preview_info[-1])

                            buffer = BytesIO()
                            if image_format in ['jpeg'] or request.rel_url.query.get('channel', '') == 'rgb':
                                img = img.convert("RGB")
                            img.save(buffer, format=image_format, quality=quality)
                            buffer.seek(0)

                            return web.Response(body=buffer.read(), content_type=f'image/{image_format}',
                                                headers={"Content-Disposition": f"filename=\"{filename}\""})

                    if 'channel' not in request.rel_url.query:
                        channel = 'rgba'
                    else:
                        channel = request.rel_url.query["channel"]

                    if channel == 'rgb':
                        with Image.open(file) as img:
                            if img.mode == "RGBA":
                                r, g, b, a = img.split()
                                new_img = Image.merge('RGB', (r, g, b))
                            else:
                                new_img = img.convert("RGB")

                            buffer = BytesIO()
                            new_img.save(buffer, format='PNG')
                            buffer.seek(0)

                            return web.Response(body=buffer.read(), content_type='image/png',
                                                headers={"Content-Disposition": f"filename=\"{filename}\""})

                    elif channel == 'a':
                        with Image.open(file) as img:
                            if img.mode == "RGBA":
                                _, _, _, a = img.split()
                            else:
                                a = Image.new('L', img.size, 255)

                            # alpha img
                            alpha_img = Image.new('RGBA', img.size)
                            alpha_img.putalpha(a)
                            alpha_buffer = BytesIO()
                            alpha_img.save(alpha_buffer, format='PNG')
                            alpha_buffer.seek(0)

                            return web.Response(body=alpha_buffer.read(), content_type='image/png',
                                                headers={"Content-Disposition": f"filename=\"{filename}\""})
                    else:
                        # Use the content type from asset resolution if available,
                        # otherwise guess from the filename.
                        content_type = (
                            resolved_content_type
                            or mimetypes.guess_type(filename)[0]
                            or 'application/octet-stream'
                        )

                        # For security, force certain mimetypes to download instead of display
                        if content_type in {'text/html', 'text/html-sandboxed', 'application/xhtml+xml', 'text/javascript', 'text/css'}:
                            content_type = 'application/octet-stream'  # Forces download

                        return web.FileResponse(
                            file,
                            headers={
                                "Content-Disposition": f"filename=\"{filename}\"",
                                "Content-Type": content_type
                            }
                        )

            return web.Response(status=404)