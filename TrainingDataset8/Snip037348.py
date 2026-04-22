def _enqueue(
        self,
        delta_type: str,
        element_proto: "Message",
        return_value: Union[None, Type[NoValue], Value] = None,
        last_index: Optional[Hashable] = None,
        element_width: Optional[int] = None,
        element_height: Optional[int] = None,
    ) -> Union["DeltaGenerator", None, Value]:
        ...