def __getattr__(self, key: str) -> Optional[str]:
        try:
            return _get_user_info()[key]
        except KeyError:
            raise AttributeError