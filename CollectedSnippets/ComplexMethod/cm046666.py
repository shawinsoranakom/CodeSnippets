def _is_gpt_oss_model(self, model_name: str = None) -> bool:
        """Check if the given (or active) model uses the gpt-oss harmony protocol."""
        name = (model_name or self.active_model_name or "").lower()
        try:
            from utils.datasets import MODEL_TO_TEMPLATE_MAPPER

            # Exact match
            if MODEL_TO_TEMPLATE_MAPPER.get(name) == "gpt-oss":
                return True
            # Partial match (e.g. name-bnb-4bit variants)
            for key, tmpl in MODEL_TO_TEMPLATE_MAPPER.items():
                if tmpl == "gpt-oss" and (key in name or name in key):
                    return True
        except Exception:
            pass
        return "gpt-oss" in name