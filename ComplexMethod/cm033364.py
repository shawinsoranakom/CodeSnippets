async def parse_webhook_request(content_type):
        """Parse request based on content-type and return structured data."""

        # 1. Query
        query_data = {k: v for k, v in request.args.items()}

        # 2. Headers
        header_data = {k: v for k, v in request.headers.items()}

        # 3. Body
        ctype = request.headers.get("Content-Type", "").split(";")[0].strip()
        if ctype and ctype != content_type:
            raise ValueError(
                f"Invalid Content-Type: expect '{content_type}', got '{ctype}'"
            )

        body_data: dict = {}

        try:
            if ctype == "application/json":
                body_data = await request.get_json() or {}

            elif ctype == "multipart/form-data":
                nonlocal canvas
                form = await request.form
                files = await request.files

                body_data = {}

                for key, value in form.items():
                    body_data[key] = value

                if len(files) > 10:
                    raise Exception("Too many uploaded files")
                for key, file in files.items():
                    desc = FileService.upload_info(
                        cvs.user_id,           # user
                        file,              # FileStorage
                        None                   # url (None for webhook)
                    )
                    file_parsed= await canvas.get_files_async([desc])
                    body_data[key] = file_parsed

            elif ctype == "application/x-www-form-urlencoded":
                form = await request.form
                body_data = dict(form)

            else:
                # text/plain / octet-stream / empty / unknown
                raw = await request.get_data()
                if raw:
                    try:
                        body_data = json.loads(raw.decode("utf-8"))
                    except Exception:
                        body_data = {}
                else:
                    body_data = {}

        except Exception:
            body_data = {}

        return {
            "query": query_data,
            "headers": header_data,
            "body": body_data,
            "content_type": ctype,
        }