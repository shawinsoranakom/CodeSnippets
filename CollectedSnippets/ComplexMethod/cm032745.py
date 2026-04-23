async def _invoke(self, **kwargs):
        """Dispatch the current file to the matching parser branch by suffix."""
        function_map = {
            "pdf": self._pdf,
            "markdown": self._markdown,
            "text&code": self._code,
            "html": self._html,
            "spreadsheet": self._spreadsheet,
            "slides": self._slides,
            "doc": self._doc,
            "docx": self._docx,
            "image": self._image,
            "audio": self._audio,
            "video": self._video,
            "email": self._email,
            "epub": self._epub,
        }

        try:
            from_upstream = ParserFromUpstream.model_validate(kwargs)
        except Exception as e:
            self.set_output("_ERROR", f"Input error: {str(e)}")
            return

        name = from_upstream.name
        if self._canvas._doc_id:
            b, n = File2DocumentService.get_storage_address(doc_id=self._canvas._doc_id)
            blob = settings.STORAGE_IMPL.get(b, n)
        else:
            blob = FileService.get_blob(from_upstream.file["created_by"], from_upstream.file["id"])

        done = False
        for p_type, conf in self._param.setups.items():
            if from_upstream.name.split(".")[-1].lower() not in conf.get("suffix", []):
                continue
            call_kwargs = dict(kwargs)
            call_kwargs.pop("name", None)
            call_kwargs.pop("blob", None)

            await thread_pool_exec(function_map[p_type], name, blob, **call_kwargs)
            done = True
            break

        if not done:
            raise Exception("No suitable for file extension: `.%s`" % from_upstream.name.split(".")[-1].lower())

        outs = self.output()
        tasks = []
        for d in outs.get("json", []):
            tasks.append(asyncio.create_task(image2id(d, partial(settings.STORAGE_IMPL.put, tenant_id=self._canvas._tenant_id), get_uuid())))

        try:
            await asyncio.gather(*tasks, return_exceptions=False)
        except Exception as e:
            logging.error("Error while parsing: %s" % e)
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise