def handle_conversation():
            """
            Handles conversation requests and streams responses back.

            Returns:
                Response: A Flask response object for streaming.
            """
            if "json" in request.form:
                json_data = request.form['json']
            else:
                json_data = request.data
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                logger.exception(e)
                return jsonify({"error": {"message": "Invalid JSON data"}}), 400
            if "proxy" in json_data:
                del json_data["proxy"]
            if json_data.get("provider") != "Custom" and "base_url" in json_data:
                del json_data["base_url"]
            if app.demo and has_crypto:
                secret = request.headers.get("x-secret", request.headers.get("x_secret"))
                if not secret or not validate_secret(secret):
                    return jsonify({"error": {"message": "Invalid or missing secret"}}), 403
            tempfiles = []
            media = []
            if "files" in request.files:
                for file in request.files.getlist('files'):
                    if file.filename != '' and is_allowed_extension(file.filename):
                        newfile = get_tempfile(file)
                        tempfiles.append(newfile)
                        media.append((Path(newfile), file.filename))
            if "media_url" in request.form:
                for url in request.form.getlist("media_url"):
                    if not _is_safe_url(url):
                        return jsonify({"error": {"message": f"Invalid or disallowed media_url: {url}"}}), 400
                    media.append((url, None))
            if media:
                json_data['media'] = media
            if app.timeout:
                json_data['timeout'] = app.timeout
            if app.stream_timeout:
                json_data['stream_timeout'] = app.stream_timeout
            if app.demo and not json_data.get("provider"):
                model = json_data.get("model")
                if model != "default" and model in models.demo_models:
                    json_data["provider"] = random.choice(models.demo_models[model][1])
                else:
                    json_data["provider"] = models.HuggingFace
            if app.demo:
                json_data["user"] = request.headers.get("x-user", "error")
                json_data["referer"] = request.headers.get("referer", "")
                json_data["user-agent"] = request.headers.get("user-agent", "")

            kwargs = self._prepare_conversation_kwargs(json_data)
            provider = kwargs.pop("provider", None)
            if provider and provider  not in Provider.__map__:
                if provider in model_map:
                    kwargs['model'] = provider
                    provider = None
                else:
                    return jsonify({"error": {"message": "Provider not found"}}), 404
            return self.app.response_class(
                safe_iter_generator(self._create_response_stream(
                    kwargs,
                    provider,
                    json_data.get("download_media", True),
                    tempfiles
                )),
                mimetype='text/event-stream'
            )