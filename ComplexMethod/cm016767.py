def _metas_to_cot(self, *, return_yaml: bool = False, **kwargs) -> str:
        user_metas = {
            k: kwargs.pop(k)
            for k in ("bpm", "duration", "keyscale", "timesignature")
            if k in kwargs
        }
        timesignature = user_metas.get("timesignature")
        if isinstance(timesignature, str) and timesignature.endswith("/4"):
            user_metas["timesignature"] = timesignature[:-2]
        user_metas = {
            k: v if not isinstance(v, str) or not v.isdigit() else int(v)
            for k, v in user_metas.items()
            if v not in {"unspecified", None}
        }
        if len(user_metas):
            meta_yaml = yaml.dump(user_metas, allow_unicode=True, sort_keys=True).strip()
        else:
            meta_yaml = ""
        return f"<think>\n{meta_yaml}\n</think>" if not return_yaml else meta_yaml