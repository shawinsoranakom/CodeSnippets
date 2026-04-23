def get_multi_range(self, ranges: list[tuple[int, int]]) -> list[bytes]:
    # HTTP range requests are inclusive
    assert all(e > s for s, e in ranges), "Range end must be greater than start"
    rs = [f"{s}-{e-1}" for s, e in ranges if e > s]

    r = self._request("GET", self._url, headers={"Range": "bytes=" + ",".join(rs)})
    if r.status not in [200, 206]:
      raise URLFileException(f"Expected 206 or 200 response {r.status} ({self._url})")

    ctype = (r.headers.get("content-type") or "").lower()
    if "multipart/byteranges" not in ctype:
      return [r.data,]

    m = re.search(r'boundary="?([^";]+)"?', ctype)
    if not m:
      raise URLFileException(f"Missing multipart boundary ({self._url})")
    boundary = m.group(1).encode()

    parts = []
    for chunk in r.data.split(b"--" + boundary):
      if b"\r\n\r\n" not in chunk:
        continue
      payload = chunk.split(b"\r\n\r\n", 1)[1].rstrip(b"\r\n")
      if payload and payload != b"--":
        parts.append(payload)
    if len(parts) != len(ranges):
      raise URLFileException(f"Expected {len(ranges)} parts, got {len(parts)} ({self._url})")
    return parts