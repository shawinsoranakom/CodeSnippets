def __init__(self, module: nn.Module, rank: int, world_size: int, device: torch.device, dtype: torch.dtype):
        """
        :param module: The module to be wrapped.
        :param rank: The rank of the current node.
        :param world_size: The number of nodes/devices the data is sharded across.
        :param device: The device of the layer.
        :param dtype: The data type of the layer.
        """
        super().__init__()

        # Initialize the properties
        self.device = device
        self.dtype = dtype
        self.module = module
        self.prev_layer = []
        self.next_layer = []
        self.is_fetched = False
        self.world_size = world_size
        self.layer_idx = -1
        self.fetch_stream = None
        self.backup_stream = None

        with torch.no_grad():
            # Collect all the parameters of the layer
            all_param_refs = [p for p in self.parameters()]

            # Store the shape of the parameters because we need it later to reconstruct them
            for p in all_param_refs:
                p._orig_shape = p.shape

            # All parameters should have the same type
            for p in all_param_refs:
                assert p.dtype == dtype, "All parameters should have same dtype"

            # Separate parameters as trainable and fixed
            self.param_refs = [[p for p in all_param_refs if p.requires_grad],
                               [p for p in all_param_refs if not p.requires_grad]]
            del all_param_refs

            # The `rank = 0` node will calculate the size each device/node should store, and
            # distribute the parameters accordingly.
            if rank == 0:
                # Merge and pad trainable (`merged_params[0]`) and fixed (`merged_params[1]`) parameters
                merged_params = [self._merge_and_pad_params(ps) for ps in self.param_refs]
                # Calculate the chunk sizes of trainable and fixed params
                self.chunk_size = [(len(p) // world_size if p is not None else 0) for p in merged_params]
                # Broadcast the sizes
                dist.broadcast(torch.tensor(self.chunk_size, device=device), src=0)
            else:
                # Create an empty tensor to receive the sizes
                chunk_size = torch.tensor([0, 0], device=device)
                # Receive the sizes
                dist.broadcast(chunk_size, src=0)
                self.chunk_size = chunk_size.tolist()

            # Create parameters for trainable (`self.chunk[0]`) and fixed (`self.chunk[1]`)
            # parameters to be stored in current device/node
            self.chunk = [nn.Parameter(self._empty((s,)), requires_grad=i == self.TRAINING_PARAMS_IDX)
                          for i, s in enumerate(self.chunk_size)]

            # An empty tensor to receive the trainable and fixed parameters combined
            chunk = self._empty((sum(self.chunk_size),))

            if rank == 0:
                # Concatenate both trainable and fixed params
                all_params = torch.cat([p.view(world_size, -1) for p in merged_params], dim=-1).view(-1)
                del merged_params

                # Scatter them to all the nodes/devices
                dist.scatter(chunk, list(all_params.split(sum(self.chunk_size))))
                del all_params
            else:
                # Receive the parameters
                dist.scatter(chunk)

            # Collect the chunk data
            chunk = chunk.split(self.chunk_size)
            for i, c in enumerate(chunk):
                self.chunk[i].data[:] = c
            del chunk

            # Cleanup the normal parameters
            self._cleanup_params()

            # Add a backward hook. This gets called when the gradients relative to the module are computed.
            self._backward_hook_ref = self.register_full_backward_hook(self._backward_hook)