def __init__(self, source: Vertex, target: Vertex, edge: EdgeData):
        self.source_id: str = source.id if source else ""
        self.target_id: str = target.id if target else ""
        self.valid_handles: bool = False
        self.target_param: str | None = None
        self._target_handle: TargetHandleDict | str | None = None
        self._data = edge.copy()
        self.is_cycle = False
        if data := edge.get("data", {}):
            self._source_handle = data.get("sourceHandle", {})
            self._target_handle = cast("TargetHandleDict", data.get("targetHandle", {}))
            self.source_handle: SourceHandle = SourceHandle(**self._source_handle)
            if isinstance(self._target_handle, dict):
                try:
                    if "name" in self._target_handle:
                        self.target_handle: TargetHandle = TargetHandle.from_loop_target_handle(
                            cast("LoopTargetHandleDict", self._target_handle)
                        )
                    else:
                        self.target_handle = TargetHandle(**self._target_handle)
                except Exception as e:
                    if "inputTypes" in self._target_handle and self._target_handle["inputTypes"] is None:
                        # Check if self._target_handle['fieldName']
                        if hasattr(target, "custom_component"):
                            display_name = getattr(target.custom_component, "display_name", "")
                            msg = (
                                f"Component {display_name} field '{self._target_handle['fieldName']}' "
                                "might not be a valid input."
                            )
                            raise ValueError(msg) from e
                        msg = (
                            f"Field '{self._target_handle['fieldName']}' on {target.display_name} "
                            "might not be a valid input."
                        )
                        raise ValueError(msg) from e
                    raise

            else:
                msg = "Target handle is not a dictionary"
                raise ValueError(msg)
            self.target_param = self.target_handle.field_name
            # validate handles
            self.validate_handles(source, target)
        else:
            # Logging here because this is a breaking change
            logger.error("Edge data is empty")
            self._source_handle = edge.get("sourceHandle", "")  # type: ignore[assignment]
            self._target_handle = edge.get("targetHandle", "")  # type: ignore[assignment]
            # 'BaseLoader;BaseOutputParser|documents|PromptTemplate-zmTlD'
            # target_param is documents
            if isinstance(self._target_handle, str):
                self.target_param = self._target_handle.split("|")[1]
                self.source_handle = None  # type: ignore[assignment]
                self.target_handle = None  # type: ignore[assignment]
            else:
                msg = "Target handle is not a string"
                raise ValueError(msg)
        # Validate in __init__ to fail fast
        self.validate_edge(source, target)