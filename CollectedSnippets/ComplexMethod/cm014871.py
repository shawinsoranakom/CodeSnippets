def _test_reduce_add_coalesced(self, tensors, buffer_size):
        dup_tensors = [tensors, [t.cuda(1) for t in tensors]]

        r_tensors = [comm.reduce_add(t) for t in zip(*dup_tensors)]
        for r, t in zip(r_tensors, tensors):
            self.assertEqualTypeString(r, t)
            self.assertEqual(r.coalesce() if r.is_sparse else r, t * 2)

        rc_tensors = comm.reduce_add_coalesced(dup_tensors, buffer_size=buffer_size)
        self.assertEqual(r_tensors, rc_tensors)
        for r, rc in zip(r_tensors, rc_tensors):
            self.assertEqualTypeString(rc, r)

        # Since we have both cuda:0 and cuda:1 inputs, the outputs must be new.
        # We can check that they have different version counters.
        # NOTE [ Version Counter in comm.*_coalesced ]
        versions = [t._version for t in rc_tensors]
        for old_version, t in zip(versions, rc_tensors):
            self.assertEqual(t._version, old_version)
            t.zero_()
            self.assertEqual(t._version, old_version + 1)