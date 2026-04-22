def __getitem__(self, key: str) -> Optional[str]:
        return _get_user_info()[key]