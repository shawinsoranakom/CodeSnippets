def get_stats(self) -> List[CacheStat]:
        stats: List[CacheStat] = []
        for session_info in self._session_info_by_id.values():
            session_state = session_info.session.session_state
            stats.extend(session_state.get_stats())
        return stats