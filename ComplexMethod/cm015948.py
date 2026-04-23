def test_total_length(self):
        padded, lengths = self._padded_sequence(torch.FloatTensor)
        max_length = max(lengths)
        packed = rnn_utils.pack_padded_sequence(padded, lengths)
        # test ValueError if total_length < max_length
        for total_length in (-1, 0, max_length - 1):
            for batch_first in (True, False):

                def err_fn():
                    rnn_utils.pad_packed_sequence(
                        packed, batch_first=batch_first, total_length=total_length
                    )

            self.assertRaisesRegex(
                ValueError,
                r"Expected total_length to be at least the "
                r"length of the longest sequence in input",
                err_fn,
            )
        # test that pad_packed_sequence returns results of correct length
        for batch_first in (True, False):
            no_extra_pad, _ = rnn_utils.pad_packed_sequence(
                packed, batch_first=batch_first
            )
            for total_length_delta in (0, 1, 8):
                total_length = max_length + total_length_delta
                unpacked, lengths_out = rnn_utils.pad_packed_sequence(
                    packed, batch_first=batch_first, total_length=total_length
                )
                self.assertEqual(lengths, lengths_out)
                self.assertEqual(unpacked.size(1 if batch_first else 0), total_length)
                if total_length_delta == 0:
                    ref_output = no_extra_pad
                elif batch_first:
                    extra_pad = no_extra_pad.new_zeros(
                        self.batch_size, total_length_delta
                    )
                    ref_output = torch.cat([no_extra_pad, extra_pad], 1)
                else:
                    extra_pad = no_extra_pad.new_zeros(
                        total_length_delta, self.batch_size
                    )
                    ref_output = torch.cat([no_extra_pad, extra_pad], 0)
                self.assertEqual(unpacked, ref_output)