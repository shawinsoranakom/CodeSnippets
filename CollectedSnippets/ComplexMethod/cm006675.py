def update_settings(self, **kwargs) -> None:
        for key, value in kwargs.items():
            # value may contain sensitive information, so we don't want to log it
            if not hasattr(self, key):
                continue
            if isinstance(getattr(self, key), list):
                # value might be a '[something]' string
                value_ = value
                with contextlib.suppress(json.decoder.JSONDecodeError):
                    value_ = orjson.loads(str(value))
                if isinstance(value_, list):
                    for item in value_:
                        item_ = str(item) if isinstance(item, Path) else item
                        if item_ not in getattr(self, key):
                            getattr(self, key).append(item_)
                else:
                    value_ = str(value_) if isinstance(value_, Path) else value_
                    if value_ not in getattr(self, key):
                        getattr(self, key).append(value_)
            else:
                setattr(self, key, value)