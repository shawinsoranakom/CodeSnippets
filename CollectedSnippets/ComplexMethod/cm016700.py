def run_up(self, layer_idx, x_ref, feat_cache, feat_idx, out_chunks):
        x = x_ref[0]
        x_ref[0] = None
        if layer_idx >= len(self.upsamples):
            for layer in self.head:
                if isinstance(layer, CausalConv3d) and feat_cache is not None:
                    cache_x = x[:, :, -CACHE_T:, :, :]
                    x = layer(x, feat_cache[feat_idx[0]])
                    feat_cache[feat_idx[0]] = cache_x
                    feat_idx[0] += 1
                else:
                    x = layer(x)
            out_chunks.append(x)
            return

        layer = self.upsamples[layer_idx]
        if feat_cache is not None:
            x = layer(x, feat_cache, feat_idx)
        else:
            x = layer(x)

        if isinstance(layer, Resample) and layer.mode == 'upsample3d' and x.shape[2] > 2:
            for frame_idx in range(0, x.shape[2], 2):
                self.run_up(
                    layer_idx + 1,
                    [x[:, :, frame_idx:frame_idx + 2, :, :]],
                    feat_cache,
                    feat_idx.copy(),
                    out_chunks,
                )
            del x
            return

        next_x_ref = [x]
        del x
        self.run_up(layer_idx + 1, next_x_ref, feat_cache, feat_idx, out_chunks)