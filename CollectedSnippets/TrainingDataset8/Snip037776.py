def save_block_message(
        self,
        block_proto: Block,
        invoked_dg_id: str,
        used_dg_id: str,
        returned_dg_id: str,
    ) -> None:
        id_to_save = self.select_dg_to_save(invoked_dg_id, used_dg_id)
        for msgs in self._cached_message_stack:
            msgs.append(BlockMsgData(block_proto, id_to_save, returned_dg_id))
        for s in self._seen_dg_stack:
            s.add(returned_dg_id)