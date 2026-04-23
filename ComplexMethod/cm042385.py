def extract(target: list[Chunk],
            sources: list[tuple[str, ChunkReader, ChunkDict]],
            out_path: str,
            progress: Callable[[int], None] | None = None):
  stats: dict[str, int] = defaultdict(int)

  mode = 'rb+' if os.path.exists(out_path) else 'wb'
  with open(out_path, mode) as out:
    for cur_chunk in target:

      # Find source for desired chunk
      for name, chunk_reader, store_chunks in sources:
        if cur_chunk.sha in store_chunks:
          bts = chunk_reader.read(store_chunks[cur_chunk.sha])

          # Check length
          if len(bts) != cur_chunk.length:
            continue

          # Check hash
          if SHA512.new(bts, truncate="256").digest() != cur_chunk.sha:
            continue

          # Write to output
          out.seek(cur_chunk.offset)
          out.write(bts)

          stats[name] += cur_chunk.length

          if progress is not None:
            progress(sum(stats.values()))

          break
      else:
        raise RuntimeError("Desired chunk not found in provided stores")

  return stats