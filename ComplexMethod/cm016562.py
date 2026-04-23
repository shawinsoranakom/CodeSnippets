def decode_tiled(self, samples, tile_x=None, tile_y=None, overlap=None, tile_t=None, overlap_t=None):
        self.throw_exception_if_invalid()
        memory_used = self.memory_used_decode(samples.shape, self.vae_dtype) #TODO: calculate mem required for tile
        model_management.load_models_gpu([self.patcher], memory_required=memory_used, force_full_load=self.disable_offload)
        dims = samples.ndim - 2
        args = {}
        if tile_x is not None:
            args["tile_x"] = tile_x
        if tile_y is not None:
            args["tile_y"] = tile_y
        if overlap is not None:
            args["overlap"] = overlap

        if dims == 1 or self.extra_1d_channel is not None:
            args.pop("tile_y")
            output = self.decode_tiled_1d(samples, **args)
        elif dims == 2:
            output = self.decode_tiled_(samples, **args)
        elif dims == 3:
            if overlap_t is None:
                args["overlap"] = (1, overlap, overlap)
            else:
                args["overlap"] = (max(1, overlap_t), overlap, overlap)
            if tile_t is not None:
                args["tile_t"] = max(2, tile_t)

            output = self.decode_tiled_3d(samples, **args)
        return output.movedim(1, -1)