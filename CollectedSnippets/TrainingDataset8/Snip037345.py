def _enqueue(  # type: ignore[misc]
        self,
        delta_type: str,
        element_proto: "Message",
        return_value: Type[NoValue],
        last_index: Optional[Hashable] = None,
        element_width: Optional[int] = None,
        element_height: Optional[int] = None,
    ) -> None:
        ...