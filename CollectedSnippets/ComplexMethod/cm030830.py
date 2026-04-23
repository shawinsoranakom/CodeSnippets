def test_framed_write_sizes_with_delayed_writer(self):
        if self.py_version < (3, 4):
            self.skipTest('not supported in Python < 3.4')

        class ChunkAccumulator:
            """Accumulate pickler output in a list of raw chunks."""
            def __init__(self):
                self.chunks = []
            def write(self, chunk):
                self.chunks.append(chunk)
            def concatenate_chunks(self):
                return b"".join(self.chunks)

        for proto in range(4, pickle.HIGHEST_PROTOCOL + 1):
            objects = [(str(i).encode('ascii'), i % 42, {'i': str(i)})
                       for i in range(int(1e4))]
            # Add a large unique ASCII string
            objects.append('0123456789abcdef' *
                           (self.FRAME_SIZE_TARGET // 16 + 1))

            # Protocol 4 packs groups of small objects into frames and issues
            # calls to write only once or twice per frame:
            # The C pickler issues one call to write per-frame (header and
            # contents) while Python pickler issues two calls to write: one for
            # the frame header and one for the frame binary contents.
            writer = ChunkAccumulator()
            self.pickler(writer, proto).dump(objects)

            # Actually read the binary content of the chunks after the end
            # of the call to dump: any memoryview passed to write should not
            # be released otherwise this delayed access would not be possible.
            pickled = writer.concatenate_chunks()
            reconstructed = self.loads(pickled)
            self.assertEqual(reconstructed, objects)
            self.assertGreater(len(writer.chunks), 1)

            # memoryviews should own the memory.
            del objects
            support.gc_collect()
            self.assertEqual(writer.concatenate_chunks(), pickled)

            n_frames = (len(pickled) - 1) // self.FRAME_SIZE_TARGET + 1
            # There should be at least one call to write per frame
            self.assertGreaterEqual(len(writer.chunks), n_frames)

            # but not too many either: there can be one for the proto,
            # one per-frame header, one per frame for the actual contents,
            # and two for the header.
            self.assertLessEqual(len(writer.chunks), 2 * n_frames + 3)

            chunk_sizes = [len(c) for c in writer.chunks]
            large_sizes = [s for s in chunk_sizes
                           if s >= self.FRAME_SIZE_TARGET]
            medium_sizes = [s for s in chunk_sizes
                           if 9 < s < self.FRAME_SIZE_TARGET]
            small_sizes = [s for s in chunk_sizes if s <= 9]

            # Large chunks should not be too large:
            for chunk_size in large_sizes:
                self.assertLess(chunk_size, 2 * self.FRAME_SIZE_TARGET,
                                chunk_sizes)
            # There shouldn't bee too many small chunks: the protocol header,
            # the frame headers and the large string headers are written
            # in small chunks.
            self.assertLessEqual(len(small_sizes),
                                 len(large_sizes) + len(medium_sizes) + 3,
                                 chunk_sizes)