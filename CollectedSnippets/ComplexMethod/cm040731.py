def _resolve(self, runtime: Runtime, custom_image_mapping: str = "") -> str:
        if runtime not in IMAGE_MAPPING:
            raise ValueError(f"Unsupported runtime {runtime}")

        if not custom_image_mapping:
            return self._default_resolve_fn(runtime)

        # Option A (pattern string that includes <runtime> to replace)
        if "<runtime>" in custom_image_mapping:
            return custom_image_mapping.replace("<runtime>", runtime)

        # Option B (json dict mapping with fallback)
        try:
            mapping: dict = json.loads(custom_image_mapping)
            # at this point we're loading the whole dict to avoid parsing multiple times
            for k, v in mapping.items():
                if k not in IMAGE_MAPPING:
                    raise ValueError(
                        f"Unsupported runtime ({runtime}) provided in LAMBDA_RUNTIME_IMAGE_MAPPING"
                    )
                self._mapping[k] = v

            if runtime in self._mapping:
                return self._mapping[runtime]

            # fall back to default behavior if the runtime was not present in the custom config
            return self._default_resolve_fn(runtime)

        except Exception:
            LOG.error(
                "Failed to load config from LAMBDA_RUNTIME_IMAGE_MAPPING=%s",
                custom_image_mapping,
            )
            raise