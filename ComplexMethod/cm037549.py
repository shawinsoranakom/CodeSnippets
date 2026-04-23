def extract_content_ids(self, input_ids: list[int]) -> list[int]:
        """
        Extract the content
        """
        has_bot_token = False
        has_eot_token = False
        bot_token_index = -1
        eot_token_index = -1
        # One for loop instead of multiple lookups
        for i, token_id in enumerate(input_ids):
            # We filter that we have multiple BOT tokens which should not
            # happen for a well prompted trained model
            if token_id == self.start_token_id and not has_bot_token:
                has_bot_token = True
                bot_token_index = i
            elif token_id == self.end_token_id:
                has_eot_token = True
                eot_token_index = i
                break

        # 1. Only BOT has been outputted
        if has_bot_token and not has_eot_token:
            # Should be = [] if model is well prompted and trained.
            return input_ids[:bot_token_index]
        # 2. Neither BOT or EOT have been outputted
        elif not has_bot_token and not has_eot_token:
            return input_ids
        # 3. Both BOT and EOT have been outputted.
        elif has_bot_token and has_eot_token:
            return input_ids[:bot_token_index] + input_ids[eot_token_index + 1 :]
        # 4. Only EOT has been outputted => this should not have occurred for a model
        #    well prompted and trained.
        else:
            return input_ids[:eot_token_index] + input_ids[eot_token_index + 1 :]