def get_models(cls, timeout: int = None, **kwargs) -> list[str]:
        if not cls._models_loaded and has_curl_cffi:
            # Try to load models from cache
            args = cls.read_args()
            if not args:
                cls.load_models_from_cache()
            if cls._models_loaded:
                return cls.models
            response = curl_cffi.get(cls.models_url, **args, timeout=timeout)
            if response.ok:
                for line in response.text.splitlines():
                    if "initialModels" not in line:
                        continue
                    line = line.split("initialModels", maxsplit=1)[-1].split("initialModelAId")[0][3:-3]
                    line = line.encode("utf-8").decode("unicode_escape")
                    models = json.loads(line)
                    cls.load_models(models)
                    cls.live += 1
                    break
                try:
                    models_path = Path(get_cookies_dir()) / ".models" / f"{secure_filename(cls.models_url)}.json"
                    models_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(models_path, "w") as f:
                        json.dump({
                            "text_models": cls.text_models,
                            "image_models": cls.image_models,
                            "video_models": cls.video_models,
                            "vision_models": cls.vision_models,
                            "models": cls.models,
                            "default_model": cls.default_model
                        }, f, indent=4)
                except Exception as e:
                    debug.error(f"Failed to cache models to {models_path}: {e}")
            else:
                cls.live -= 1
                cls.load_models_from_cache()
                debug.log(f"Failed to load models from {cls.url}: {response.status_code} {response.reason}")
        return cls.models