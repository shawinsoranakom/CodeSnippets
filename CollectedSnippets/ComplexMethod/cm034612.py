async def iter_lines(iter_response: AsyncIterator[bytes], delimiter=None):
    """
    iterate streaming content line by line, separated by ``\\n``.

    Copied from: https://requests.readthedocs.io/en/latest/_modules/requests/models/
    which is under the License: Apache 2.0
    """
    pending = None

    async for chunk in iter_response:
        if pending is not None:
            chunk = pending + chunk
        lines = chunk.split(delimiter) if delimiter else chunk.splitlines()
        pending = (
            lines.pop()
            if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]
            else None
        )

        for line in lines:
            yield line

    if pending is not None:
        yield pending