def poll_events(self):
        """Generalized poller for streams such as Kinesis or DynamoDB
        Examples of Kinesis consumers:
        * StackOverflow: https://stackoverflow.com/a/22403036/6875981
        * AWS Sample: https://github.com/aws-samples/kinesis-poster-worker/blob/master/worker.py
        Examples of DynamoDB consumers:
        * Blogpost: https://www.tecracer.com/blog/2022/05/getting-a-near-real-time-view-of-a-dynamodb-stream-with-python.html
        """
        # TODO: consider potential shard iterator timeout after 300 seconds (likely not relevant with short-polling):
        #   https://docs.aws.amazon.com/streams/latest/dev/troubleshooting-consumers.html#shard-iterator-expires-unexpectedly
        #  Does this happen if no records are received for 300 seconds?
        if not self.shards:
            self.shards = self.initialize_shards()

        if not self.shards:
            LOG.debug("No shards found for %s.", self.source_arn)
            raise EmptyPollResultsException(service=self.event_source(), source_arn=self.source_arn)
        else:
            # Remove all shard batchers without corresponding shards
            for shard_id in self.shard_batcher.keys() - self.shards.keys():
                self.shard_batcher.pop(shard_id, None)

        # TODO: improve efficiency because this currently limits the throughput to at most batch size per poll interval
        # Handle shards round-robin. Re-initialize current shard iterator once all shards are handled.
        if self.iterator_over_shards is None:
            self.iterator_over_shards = iter(self.shards.items())

        current_shard_tuple = next(self.iterator_over_shards, None)
        if not current_shard_tuple:
            self.iterator_over_shards = iter(self.shards.items())
            current_shard_tuple = next(self.iterator_over_shards, None)

        # TODO Better handling when shards are initialised and the iterator returns nothing
        if not current_shard_tuple:
            raise PipeInternalError(
                "Failed to retrieve any shards for stream polling despite initialization."
            )

        try:
            self.poll_events_from_shard(*current_shard_tuple)
        except PipeInternalError:
            # TODO: standardize logging
            # Ignore and wait for the next polling interval, which will do retry
            pass