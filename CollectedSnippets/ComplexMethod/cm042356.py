def unsparsify(f: StreamingDecompressor) -> Generator[bytes, None, None]:
  # https://source.android.com/devices/bootloader/images#sparse-format
  magic = struct.unpack("I", f.read(4))[0]
  assert(magic == 0xed26ff3a)

  # Version
  major = struct.unpack("H", f.read(2))[0]
  minor = struct.unpack("H", f.read(2))[0]
  assert(major == 1 and minor == 0)

  f.read(2)  # file header size
  f.read(2)  # chunk header size

  block_sz = struct.unpack("I", f.read(4))[0]
  f.read(4)  # total blocks
  num_chunks = struct.unpack("I", f.read(4))[0]
  f.read(4)  # crc checksum

  for _ in range(num_chunks):
    chunk_type, out_blocks = SPARSE_CHUNK_FMT.unpack(f.read(12))

    if chunk_type == 0xcac1:  # Raw
      # TODO: yield in smaller chunks. Yielding only block_sz is too slow. Largest observed data chunk is 252 MB.
      yield f.read(out_blocks * block_sz)
    elif chunk_type == 0xcac2:  # Fill
      filler = f.read(4) * (block_sz // 4)
      for _ in range(out_blocks):
        yield filler
    elif chunk_type == 0xcac3:  # Don't care
      yield b""
    else:
      raise Exception("Unhandled sparse chunk type")