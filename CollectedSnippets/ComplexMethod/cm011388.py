def handle_view(args, kwargs) -> "LocalShardsWrapper":
        view_shape = args[1]
        res_shards_list = []
        if len(args[0].local_shards()) > 1:
            if args[0].local_shards()[0].ndim == 2:
                if not (
                    args[0].storage_metadata().size[0] == view_shape[0]
                    and args[0].storage_metadata().size[1] == view_shape[1]
                ):
                    raise AssertionError
                # This accounts for a DTensor quirk, when multiple shards are present on a rank, DTensor on
                # init calls view_as() on the global tensor shape
                # will fail because the view shape is not applicable to individual shards.
                res_shards_list = [
                    aten.view.default(shard, shard.shape, **kwargs)
                    for shard in args[0].local_shards()
                ]
            elif args[0].local_shards()[0].ndim == 1:
                if args[0].storage_metadata().size[0] != view_shape[0]:
                    raise AssertionError
                # This case is for optimizer sharding as regardless of sharding type, optimizer state is row wise sharded
                res_shards_list = [
                    aten.view.default(shard, shard.shape, **kwargs)
                    for shard in args[0].local_shards()
                ]
            else:
                raise NotImplementedError("No support for view on tensors ndim > 2")
        else:
            # view is called per shard
            res_shards_list = [
                aten.view.default(shard, args[1], **kwargs)
                for shard in args[0].local_shards()
            ]
        return LocalShardsWrapper(res_shards_list, args[0].local_offsets())