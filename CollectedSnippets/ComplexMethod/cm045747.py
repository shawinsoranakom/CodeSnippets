def _corrupt_mongodb_resume_token(pstorage_path: pathlib.Path) -> None:
    """Overwrite the MongoDbOplogToken bytes in persistence snapshot files with 0xFF.

    Snapshot files are LZ4-compressed bincode sequences of Event enums.  The
    relevant pattern in the decompressed bytes is:

        OffsetKey::MongoDb      (u32 LE variant 4)  -> 04 00 00 00
        OffsetValue::MongoDbOplogToken (u32 LE variant 11) -> 0b 00 00 00
        token length            (u64 LE)             -> 8 bytes
        token bytes             (Vec<u8>)             -> <length> bytes   <- corrupted

    Replacing the token bytes with 0xFF makes the BSON invalid, so
    bson::from_slice will fail in initialize() and the connector returns
    ReadError::MalformedData.
    """
    # bincode encodes OffsetKey::MongoDb (variant 4) then
    # OffsetValue::MongoDbOplogToken (variant 11) as consecutive u32 LE values.
    PATTERN = b"\x04\x00\x00\x00\x0b\x00\x00\x00"

    streams_dir = pstorage_path / "streams"
    corrupted = False
    for chunk_file in streams_dir.rglob("*"):
        if not chunk_file.is_file():
            continue
        try:
            int(chunk_file.name)  # snapshot chunks are named by numeric id
        except ValueError:
            continue

        raw = chunk_file.read_bytes()
        orig_size = struct.unpack_from("<I", raw)[0]
        data = bytearray(lz4.block.decompress(raw[4:], uncompressed_size=orig_size))

        # Corrupt every occurrence in this chunk (multiple AdvanceTime events
        # may each carry a token; the engine uses the latest one it finds).
        offset = 0
        while True:
            pos = data.find(PATTERN, offset)
            if pos == -1:
                break

            # u64 LE token length immediately follows the 8-byte pattern
            token_len = struct.unpack_from("<Q", data, pos + len(PATTERN))[0]
            token_start = pos + len(PATTERN) + 8
            for i in range(token_start, token_start + token_len):
                data[i] = 0xFF
            corrupted = True
            offset = token_start + token_len

        if corrupted:
            recompressed = lz4.block.compress(bytes(data), store_size=False)
            chunk_file.write_bytes(struct.pack("<I", len(data)) + recompressed)

    if not corrupted:
        raise AssertionError("No MongoDB resume token found in persistence files")