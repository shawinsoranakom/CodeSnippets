def __post_init__(self):
        # Infer default license from the checkpoint used, if possible.
        if (
            self.license is None
            and not is_offline_mode()
            and self.finetuned_from is not None
            and len(self.finetuned_from) > 0
        ):
            try:
                info = model_info(self.finetuned_from)
                for tag in info.tags:
                    if tag.startswith("license:"):
                        self.license = tag[8:]
            except (httpx.HTTPError, HFValidationError, OfflineModeIsEnabled):
                pass