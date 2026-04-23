def fetch_params(self):
        """
        ### Fetch the parameters from all shards

        This will fetch all the parameter data from all the nodes and rebuild the parameters on each node.
        """

        # Skip is already fetched
        if self.is_fetched:
            return

        # Set the flag
        self.is_fetched = True

        # Skip if there's nothing to fetch or share.
        if sum(self.chunk_size) == 0:
            return

        # Use `fetch_stream` to fetch the parameters from all the shards
        with torch.cuda.stream(self.fetch_stream):
            # Create an empty tensor to receive the parameters
            buffer = self._empty((self.world_size * sum(self.chunk_size),))
            # Split the continuous buffer into the number of nodes. These splits are views of `buffer'.
            buffers = list(buffer.split(sum(self.chunk_size)))

            # Concatenate both trainable and fixed chunks
            chunk = torch.cat(self.chunk, dim=0)

            # Gather the parameters from all the nodes/devices
            dist.all_gather(buffers, chunk)

            # Split the gathered parameters into the trainable and fixed chunks
            params = buffer.view(-1, sum(self.chunk_size)).split(self.chunk_size, dim=1)
            # Wait for the gather operation to complete and then clear the references to the buffers
            buffer.record_stream(self.fetch_stream)
            for b in buffers:
                b.record_stream(self.fetch_stream)
            buffer.record_stream(self.fetch_stream)
            del buffer
            del buffers

            # Reshape the trainable and fixed parameters to continuous tensors
            params = [p.reshape(-1) for p in params]

            # Collect the individual parameter tensors
            for cont, ps in zip(params, self.param_refs):
                # If there are no parameters, skip
                if not ps:
                    continue

                # Offset of the continuous tensor
                offset = 0
                # Iterate through model parameters and assign the values from the continuous tensor
                for p in ps:
                    # Original parameter shape
                    shape = p._orig_shape  # type: ignore[attr-defined]
                    # Change the storage size of the parameter. This was set to $0$ when we cleaned up the parameters.
                    p.data.storage().resize_(shape.numel())
                    # Assign the values from the continuous tensor
                    p.data[:] = cont[offset: offset + shape.numel()].reshape(shape)
                    # Wait for the operations to complete before other operations can be performed
                    p.data.record_stream(self.fetch_stream)
                    # Update the offset
                    offset += shape.numel()

                # Wait for the operation to complete before other operations can be performed
                cont.record_stream(self.fetch_stream)

            #
            del params