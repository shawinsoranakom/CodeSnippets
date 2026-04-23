def _get_rpb_matrix(self, reference_boxes, feat_size):
        """Get the relative position bias (RPB) matrix for box-relative position bias."""
        H, W = feat_size
        boxes_xyxy = xywh2xyxy(reference_boxes).transpose(0, 1)
        bs, num_queries, _ = boxes_xyxy.shape
        if self.compilable_cord_cache is None:
            self.compilable_cord_cache = self._get_coords(H, W, reference_boxes.device, reference_boxes.dtype)
            self.compilable_stored_size = (H, W)

        if torch.compiler.is_dynamo_compiling() or self.compilable_stored_size == (
            H,
            W,
        ):
            # good, hitting the cache, will be compilable
            coords_h, coords_w = self.compilable_cord_cache
        else:
            # cache miss, will create compilation issue
            # In case we're not compiling, we'll still rely on the dict-based cache
            if feat_size not in self.coord_cache:
                self.coord_cache[feat_size] = self._get_coords(H, W, reference_boxes.device, reference_boxes.dtype)
            coords_h, coords_w = self.coord_cache[feat_size]

            assert coords_h.shape == (H,)
            assert coords_w.shape == (W,)

        deltas_y = coords_h.view(1, -1, 1) - boxes_xyxy.reshape(-1, 1, 4)[:, :, 1:4:2]
        deltas_y = deltas_y.view(bs, num_queries, -1, 2)
        deltas_x = coords_w.view(1, -1, 1) - boxes_xyxy.reshape(-1, 1, 4)[:, :, 0:3:2]
        deltas_x = deltas_x.view(bs, num_queries, -1, 2)

        if self.boxRPB in ["log", "both"]:
            deltas_x_log = deltas_x * 8  # normalize to -8, 8
            deltas_x_log = torch.sign(deltas_x_log) * torch.log2(torch.abs(deltas_x_log) + 1.0) / np.log2(8)

            deltas_y_log = deltas_y * 8  # normalize to -8, 8
            deltas_y_log = torch.sign(deltas_y_log) * torch.log2(torch.abs(deltas_y_log) + 1.0) / np.log2(8)
            if self.boxRPB == "log":
                deltas_x = deltas_x_log
                deltas_y = deltas_y_log
            else:
                deltas_x = torch.cat([deltas_x, deltas_x_log], dim=-1)
                deltas_y = torch.cat([deltas_y, deltas_y_log], dim=-1)

        if self.training:
            assert self.use_act_checkpoint, "activation ckpt not enabled in decoder"
        deltas_x = self.boxRPB_embed_x(x=deltas_x)  # bs, num_queries, W, n_heads
        deltas_y = self.boxRPB_embed_y(x=deltas_y)  # bs, num_queries, H, n_heads

        if not torch.compiler.is_dynamo_compiling():
            assert deltas_x.shape[:3] == (bs, num_queries, W)
            assert deltas_y.shape[:3] == (bs, num_queries, H)

        B = deltas_y.unsqueeze(3) + deltas_x.unsqueeze(2)  # bs, num_queries, H, W, n_heads
        if not torch.compiler.is_dynamo_compiling():
            assert B.shape[:4] == (bs, num_queries, H, W)
        B = B.flatten(2, 3)  # bs, num_queries, H*W, n_heads
        B = B.permute(0, 3, 1, 2)  # bs, n_heads, num_queries, H*W
        B = B.contiguous()  # memeff attn likes ordered strides
        if not torch.compiler.is_dynamo_compiling():
            assert B.shape[2:] == (num_queries, H * W)
        return B