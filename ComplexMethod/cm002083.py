def test_dia_delay_pattern(self):
        def check_eos_logits(out, logits, batch, channel, eos):
            for i in range(vocab):
                if i == eos:
                    self.assertTrue(out[batch, channel, i] == 0)
                else:
                    self.assertTrue(out[batch, channel, i] == -float("inf"))

            for c in range(channel):
                if c != channel:
                    self.assertTrue((out[batch, c] == logits[batch, c]).all())

        eos = 2
        delay_pattern = [0, 2, 3]
        max_generation_len = 10
        bsz, channels, vocab = 2, 3, 4

        input_ids = torch.LongTensor([[0]])
        logits = torch.zeros(size=(bsz, channels, vocab))
        # Ensure that argmax can not result in eos
        logits[:, :, eos] = -1

        delay_pattern_processor = DiaEOSDelayPatternLogitsProcessor(
            delay_pattern=delay_pattern, eos_token_id=eos, max_generation_len=max_generation_len
        )
        out = delay_pattern_processor(input_ids, logits.clone()).view(bsz, channels, vocab)

        # Nothing should happen except for init of some attributes
        self.assertTrue((out == logits).all())
        self.assertTrue((~delay_pattern_processor.active_batches).all())
        self.assertTrue(
            (delay_pattern_processor.delay_pattern == torch.tensor([delay_pattern for _ in range(bsz)])).all()
        )

        # Make first batch end
        logits[0, 0, eos] = 1

        # Go through the complete delay pattern
        for i in range(max(delay_pattern) + 1):
            out = delay_pattern_processor(input_ids, logits.clone()).view(bsz, channels, vocab)

            # no delay should kick in
            if i == 1:
                self.assertTrue((out == logits).all())
            else:
                j = i if i == 0 else i - 1
                check_eos_logits(out=out, logits=logits, batch=0, channel=j, eos=eos)
                self.assertTrue((out[1] == logits[1]).all())
                self.assertTrue(delay_pattern_processor.active_batches[0])
                self.assertFalse(delay_pattern_processor.active_batches[1])
                self.assertTrue(
                    (
                        delay_pattern_processor.delay_pattern[0]
                        == torch.tensor([delay - (i + 1) for delay in delay_pattern])
                    ).all()
                )
                self.assertTrue((delay_pattern_processor.delay_pattern[1] == torch.tensor(delay_pattern)).all())

        # Make second batch end
        logits[1, 0, eos] = 1

        # Just to check if other batches could work
        out = delay_pattern_processor(input_ids, logits.clone()).view(bsz, channels, vocab)

        self.assertTrue((out[0] == logits[0]).all())
        self.assertTrue(delay_pattern_processor.active_batches.all())
        self.assertTrue(
            (delay_pattern_processor.delay_pattern[0] == torch.tensor([delay - 5 for delay in delay_pattern])).all()
        )
        self.assertTrue(
            (delay_pattern_processor.delay_pattern[1] == torch.tensor([delay - 1 for delay in delay_pattern])).all()
        )

        # Last check on max generation length reached (with delay in mind until last channel produces eos)
        input_ids = torch.LongTensor([[0] * (max_generation_len - max(delay_pattern) - 1)])
        delay_pattern_processor = DiaEOSDelayPatternLogitsProcessor(
            delay_pattern=delay_pattern, eos_token_id=eos, max_generation_len=max_generation_len
        )
        out = delay_pattern_processor(input_ids, logits.clone()).view(bsz, channels, vocab)

        check_eos_logits(out=out, logits=logits, batch=0, channel=0, eos=eos)
        check_eos_logits(out=out, logits=logits, batch=1, channel=0, eos=eos)
        self.assertTrue(delay_pattern_processor.active_batches.all())
        self.assertTrue((delay_pattern_processor.delay_pattern == torch.tensor(delay_pattern) - 1).all())