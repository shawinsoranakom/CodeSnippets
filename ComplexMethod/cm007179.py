def get_artifact_type(value, build_result) -> str:
    result = ArtifactType.UNKNOWN
    match value:
        case Data():
            result = ArtifactType.RECORD

        case str():
            result = ArtifactType.TEXT

        case dict():
            result = ArtifactType.OBJECT

        case list():
            result = ArtifactType.ARRAY

        case Message():
            result = ArtifactType.MESSAGE

    if result == ArtifactType.UNKNOWN and (
        isinstance(build_result, Generator) or (isinstance(value, Message) and isinstance(value.text, Generator))
    ):
        result = ArtifactType.STREAM

    return result.value