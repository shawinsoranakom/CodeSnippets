def file_uploader(
        self,
        label: str,
        type: Optional[Union[str, List[str]]],
        accept_multiple_files: Literal[True],
        key: Optional[Key] = None,
        help: Optional[str] = None,
        on_change: Optional[WidgetCallback] = None,
        args: Optional[WidgetArgs] = None,
        kwargs: Optional[WidgetKwargs] = None,
        *,
        disabled: bool = False,
        label_visibility: LabelVisibility = "visible",
    ) -> Optional[List[UploadedFile]]:
        ...