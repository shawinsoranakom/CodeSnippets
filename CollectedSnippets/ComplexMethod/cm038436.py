def __post_init__(self):
        if self.ipc_handles_pickled is not None:
            if self.ipc_handles is not None:
                raise ValueError(
                    "Cannot specify both `ipc_handles` and `ipc_handles_pickled`"
                )

            if not envs.VLLM_ALLOW_INSECURE_SERIALIZATION:
                raise ValueError(
                    "Refusing to deserialize `ipc_handles_pickled` without "
                    "VLLM_ALLOW_INSECURE_SERIALIZATION=1"
                )

            self.ipc_handles = pickle.loads(base64.b64decode(self.ipc_handles_pickled))
            self.ipc_handles_pickled = None

        if self.ipc_handles is None:
            raise ValueError(
                "Either `ipc_handles` or `ipc_handles_pickled` must be provided"
            )

        num_params = len(self.names)
        if len(self.dtype_names) != num_params:
            raise ValueError(
                f"`dtype_names` should be of the same size as `names`: "
                f"got {len(self.dtype_names)} and {len(self.names)}"
            )
        if len(self.shapes) != num_params:
            raise ValueError(
                f"`shapes` should be of the same size as `names`: "
                f"got {len(self.shapes)} and {len(self.names)}"
            )
        if len(self.ipc_handles) != num_params:
            raise ValueError(
                f"`ipc_handles` should be of the same size as `names`: "
                f"got {len(self.ipc_handles)} and {len(self.names)}"
            )