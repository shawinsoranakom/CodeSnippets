def _annotation_is_complex(annotation: type[Any] | None) -> bool:
    return (
        lenient_issubclass(annotation, (BaseModel, Mapping, UploadFile))
        or _annotation_is_sequence(annotation)
        or is_dataclass(annotation)
    )