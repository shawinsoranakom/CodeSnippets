def get_stats(self) -> List[CacheStat]:
        stat = CacheStat("st_session_state", "", asizeof(self))
        return [stat]