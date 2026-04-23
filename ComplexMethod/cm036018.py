def sample(self):
        """
        ### Evaluation

        We use the sampling function to evaluate the model on a set of problems
        """

        # Skip in the first epoch
        if self.training_loop.idx < 1:
            return

        # Create a dataset to generate problems
        dataset = ArithmeticDataset(self.seq_len, self.max_digits, 1)
        # Get a set of problems and answers
        qa = [dataset.get_qa() for _ in range(self.n_tests)]
        # Collect the problems only
        questions = [p[0] for p in qa]

        # Create a tensor with only the initial token
        data = torch.tensor([[dataset.stoi[p[0]] for p in questions]])
        # Move to device
        data = data.to(self.device)

        # Number of sequences that have completed
        finished = torch.zeros((len(questions),)).bool().to(self.device)
        # Token id of the new line character - this marks end of the answer
        new_line = dataset.stoi['\n']

        # Sampled results
        results = [p[0] for p in questions]

        # Sample upto sequence length
        for i in monit.iterate('Sample', self.seq_len - 1):
            # If all the sequences have completed we skip this
            if finished.sum() == len(finished):
                continue

            # Get the model output
            output, *_ = self.model(data)
            # Get the model prediction (greedy)
            output = output[-1].argmax(dim=-1)

            # Find which sequences have finished
            finished = finished | (output == new_line)
            # Skip if all have finished
            if finished.sum() == len(finished):
                continue

            # Override with the question
            for j, p in enumerate(questions):
                if len(p) > i + 1:
                    output[j] = dataset.stoi[p[i + 1]]

            # Add the next token to the input
            data = torch.cat([data, output[None, :]], dim=0)

            # Get the sampled results
            for j, c in enumerate(output):
                results[j] += dataset.itos[c]

        # Discard everything after the answer in the results
        results = [r.split('\n')[0] for r in results]

        # Log a sample
        res_sample = results[0].split(';')
        logger.log([(res_sample[0], Text.key), (';', Text.subtle), (';'.join(res_sample[1:]), Text.none)])

        # Get the answers
        results = [r.split('x==')[-1] for r in results]

        # Count the number of correct answers
        correct = 0
        for r, _qa in zip(results, qa):
            if r == _qa[1]:
                correct += 1

        # Log the score
        tracker.save('score', correct / len(results))