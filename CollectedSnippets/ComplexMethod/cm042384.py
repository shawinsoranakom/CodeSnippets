def parse_caibx(caibx_path: str) -> list[Chunk]:
  """Parses the chunks from a caibx file. Can handle both local and remote files.
  Returns a list of chunks with hash, offset and length"""
  caibx: io.BufferedIOBase
  if os.path.isfile(caibx_path):
    caibx = open(caibx_path, 'rb')
  else:
    resp = requests.get(caibx_path, timeout=CAIBX_DOWNLOAD_TIMEOUT)
    resp.raise_for_status()
    caibx = io.BytesIO(resp.content)

  caibx.seek(0, os.SEEK_END)
  caibx_len = caibx.tell()
  caibx.seek(0, os.SEEK_SET)

  # Parse header
  length, magic, flags, min_size, _, max_size = struct.unpack("<QQQQQQ", caibx.read(CA_HEADER_LEN))
  assert flags == flags
  assert length == CA_HEADER_LEN
  assert magic == CA_FORMAT_INDEX

  # Parse table header
  length, magic = struct.unpack("<QQ", caibx.read(CA_TABLE_HEADER_LEN))
  assert magic == CA_FORMAT_TABLE

  # Parse chunks
  num_chunks = (caibx_len - CA_HEADER_LEN - CA_TABLE_MIN_LEN) // CA_TABLE_ENTRY_LEN
  chunks = []

  offset = 0
  for i in range(num_chunks):
    new_offset = struct.unpack("<Q", caibx.read(8))[0]

    sha = caibx.read(32)
    length = new_offset - offset

    assert length <= max_size

    # Last chunk can be smaller
    if i < num_chunks - 1:
      assert length >= min_size

    chunks.append(Chunk(sha, offset, length))
    offset = new_offset

  caibx.close()
  return chunks