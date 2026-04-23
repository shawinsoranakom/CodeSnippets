def __iter__(self) -> Iterator[str]:
        return iter(_get_user_info())