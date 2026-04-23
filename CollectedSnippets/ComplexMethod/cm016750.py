def _down_encode(self, x, r_embed, clip, transformer_options={}):
        level_outputs = []
        block_group = zip(self.down_blocks, self.down_downscalers, self.down_repeat_mappers)
        for down_block, downscaler, repmap in block_group:
            x = downscaler(x)
            for i in range(len(repmap) + 1):
                for block in down_block:
                    if isinstance(block, ResBlock) or (
                            hasattr(block, '_fsdp_wrapped_module') and isinstance(block._fsdp_wrapped_module,
                                                                                  ResBlock)):
                        x = block(x)
                    elif isinstance(block, AttnBlock) or (
                            hasattr(block, '_fsdp_wrapped_module') and isinstance(block._fsdp_wrapped_module,
                                                                                  AttnBlock)):
                        x = block(x, clip, transformer_options=transformer_options)
                    elif isinstance(block, TimestepBlock) or (
                            hasattr(block, '_fsdp_wrapped_module') and isinstance(block._fsdp_wrapped_module,
                                                                                  TimestepBlock)):
                        x = block(x, r_embed)
                    else:
                        x = block(x)
                if i < len(repmap):
                    x = repmap[i](x)
            level_outputs.insert(0, x)
        return level_outputs