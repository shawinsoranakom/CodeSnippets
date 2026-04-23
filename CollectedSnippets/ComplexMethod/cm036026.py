def merge_compress_memory(self, mem: CompressedMemory, new_mem: List[torch.Tensor]) \
            -> Tuple[CompressedMemory, List[torch.Tensor]]:
        """
        Concatenate new memories and compress the oldest memories.
        """

        # If the configurations specify not to use memory
        if self.mem_len == 0 and self.c_mem_len == 0:
            return CompressedMemory([], []), []

        # Get memory and compressed memory
        if mem is not None:
            mem, c_mem = mem.mem, mem.c_mem
        else:
            mem, c_mem = [], []

        # Concatenate new memories with old memory
        if mem:
            mem = [torch.cat((m, x), dim=0) for m, x in zip(mem, new_mem)]
        else:
            mem = new_mem

        # Compress the oldest memories if there are more memories than `mem_len`
        if len(mem[0]) > self.mem_len:
            # Calculate the number of compressed memories to make $n_{cm} = \bigg\lceil\frac{n'_m - N_m}{c}\bigg\rceil$,
            # where $n'_m$ is the number of memories we have
            # and $N_m$ is the maximum number of memories we maintain (`mem_len`).
            n_c_mem = (len(mem[0]) - self.mem_len + self.compression_rate - 1) // self.compression_rate
            # Number of memories to compress $c n_{cm}$
            n_old = n_c_mem * self.compression_rate
            # A list to keep memories that need to be compressed for each layer.
            mem_to_compress = []
            # A list to keep the memories that do not get compressed for each layer.
            uncompressed_mem = []
            # Iterate through memories of each layer.
            for m in mem:
                # Split the memories at $c n_{cm}$
                cm, m = torch.split(m, [n_old, len(m) - n_old])
                # Collect memories to compress
                mem_to_compress.append(cm)
                # Collect remaining memories
                uncompressed_mem.append(m)
            # Update the memories
            mem = uncompressed_mem

            # Compress the memories
            new_c_mem = []
            for i, layer in enumerate(self.model.transformer.layers):
                new_c_mem.append(layer.compress(mem_to_compress[i]))

            # Concatenate newly compressed memories with old compressed memories
            if c_mem:
                c_mem = [torch.cat((m, nm), dim=0) for m, nm in zip(c_mem, new_c_mem)]
            # If there are no old compressed memories
            else:
                c_mem = new_c_mem

            # Truncate old memories
            if len(c_mem[0]) > self.c_mem_len:
                c_mem = [m[-self.c_mem_len:] for m in c_mem]
        # No memories are compressed if the number of memories is less than `mem_len`
        else:
            mem_to_compress = []

        # Return memories and the memories that were compressed.
        # Memories that were compressed are needed for the reconstruction loss computation.
        return CompressedMemory(mem, c_mem), mem_to_compress