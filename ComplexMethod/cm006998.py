async def _fetch_openrouter_models_data(self) -> None:
        """Fetch all models from OpenRouter API and cache them along with name mappings."""
        if self._models_api_cache and self._model_name_to_api_id:
            return

        if not self.use_openrouter_specs:
            self.log("OpenRouter specs are disabled. Skipping fetch.")
            return

        try:
            self.status = "Fetching OpenRouter model specifications..."
            self.log("Fetching all model specifications from OpenRouter API: https://openrouter.ai/api/v1/models")
            async with (
                aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session,
                session.get("https://openrouter.ai/api/v1/models") as response,
            ):
                if response.status == http.HTTPStatus.OK:
                    data = await response.json()
                    models_list = data.get("data", [])

                    _models_api_cache_temp = {}
                    _model_name_to_api_id_temp = {}

                    for model_data in models_list:
                        api_model_id = model_data.get("id")
                        if not api_model_id:
                            continue

                        _models_api_cache_temp[api_model_id] = model_data
                        _model_name_to_api_id_temp[api_model_id] = api_model_id

                        api_model_name = model_data.get("name")
                        if api_model_name:
                            _model_name_to_api_id_temp[api_model_name] = api_model_id
                            simplified_api_name = self._simplify_model_name(api_model_name)
                            _model_name_to_api_id_temp[simplified_api_name] = api_model_id

                        hugging_face_id = model_data.get("hugging_face_id")
                        if hugging_face_id:
                            _model_name_to_api_id_temp[hugging_face_id] = api_model_id
                            simplified_hf_id = self._simplify_model_name(hugging_face_id)
                            _model_name_to_api_id_temp[simplified_hf_id] = api_model_id

                        if "/" in api_model_id:
                            try:
                                model_name_part_of_id = api_model_id.split("/", 1)[1]
                                if model_name_part_of_id:
                                    _model_name_to_api_id_temp[model_name_part_of_id] = api_model_id
                                    simplified_part_id = self._simplify_model_name(model_name_part_of_id)
                                    _model_name_to_api_id_temp[simplified_part_id] = api_model_id
                            except IndexError:
                                pass  # Should not happen if '/' is present

                    self._models_api_cache = _models_api_cache_temp
                    self._model_name_to_api_id = _model_name_to_api_id_temp
                    log_msg = (
                        f"Successfully fetched and cached {len(self._models_api_cache)} "
                        f"model specifications from OpenRouter."
                    )
                    self.log(log_msg)
                else:
                    err_text = await response.text()
                    self.log(f"Failed to fetch OpenRouter models: HTTP {response.status} - {err_text}")
                    self._models_api_cache = {}
                    self._model_name_to_api_id = {}
        except aiohttp.ClientError as e:
            self.log(f"AIOHTTP ClientError fetching OpenRouter models: {e!s}", "error")
            self._models_api_cache = {}
            self._model_name_to_api_id = {}
        except asyncio.TimeoutError:
            self.log("Timeout fetching OpenRouter model specifications.", "error")
            self._models_api_cache = {}
            self._model_name_to_api_id = {}
        except json.JSONDecodeError as e:
            self.log(f"JSON decode error fetching OpenRouter models: {e!s}", "error")
            self._models_api_cache = {}
            self._model_name_to_api_id = {}
        finally:
            self.status = ""