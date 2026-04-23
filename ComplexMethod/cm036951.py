def test_two_token_bad_word(self, vllm_runner):
        with vllm_runner(self.MODEL, dtype="half") as llm:
            output_token_ids = self._generate(llm)
            assert output_token_ids[:2] == [
                self.target_token_id1,
                self.target_token_id2,
            ]

            output_token_ids = self._generate(llm, bad_words=[self.TARGET_TOKEN1])
            assert self.target_token_id1 not in output_token_ids

            output_token_ids = self._generate(llm, bad_words=[self.TARGET_TOKEN2])
            assert output_token_ids[0] == self.target_token_id1
            assert self.target_token_id2 not in output_token_ids

            output_token_ids = self._generate(
                llm, bad_words=[f"{self.TARGET_TOKEN1} {self.TARGET_TOKEN2}"]
            )
            assert output_token_ids[0] == self.target_token_id1
            assert output_token_ids[:2] != [
                self.target_token_id1,
                self.target_token_id2,
            ]
            assert not self._contains(
                output_token_ids, [self.target_token_id1, self.target_token_id2]
            )
            # Model dependent behaviour
            assert output_token_ids[:2] == [
                self.target_token_id1,
                self.neighbour_token_id2,
            ]

            output_token_ids = self._generate(
                llm,
                bad_words=[
                    f"{self.TARGET_TOKEN1} {self.TARGET_TOKEN2}",
                    f"{self.TARGET_TOKEN1} {self.NEIGHBOUR_TOKEN2}",
                ],
            )
            assert output_token_ids[0] == self.target_token_id1
            assert output_token_ids[:2] != [
                self.target_token_id1,
                self.target_token_id2,
            ]
            assert not self._contains(
                output_token_ids, [self.target_token_id1, self.target_token_id2]
            )
            assert output_token_ids[:2] != [
                self.target_token_id1,
                self.neighbour_token_id2,
            ]
            assert not self._contains(
                output_token_ids, [self.target_token_id1, self.neighbour_token_id2]
            )
            assert (self.target_token_id2 in output_token_ids) or (
                self.neighbour_token_id2 in output_token_ids
            )