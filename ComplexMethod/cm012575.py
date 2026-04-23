def __init__(
        self,
        input_nodes,
        layout: ir.Layout,
        scale,
        score_mod,
        mask_mod,
        kv_block_size,
        q_block_size,
        has_other_buffer,
        no_full_kv_block,
        fake_buffers,
        len_score_other,
        len_mask_other,
        kernel_input_name_to_buffer,
        block_vars,
    ) -> None:
        assert layout.dtype in [torch.float, torch.bfloat16, torch.float16]
        super().__init__("flex_attention", input_nodes, layout, parallel_num_threads())
        self.scale = scale
        self.score_mod = score_mod
        self.mask_mod = mask_mod
        self.score_buf_name = (
            V.graph.register_buffer(self.score_mod) if self.score_mod else None
        )
        self.mask_buf_name = (
            V.graph.register_buffer(self.mask_mod) if self.mask_mod else None
        )

        def get_idx(buf_name):
            match = re.search(r"\d+", buf_name)
            assert match, f"incorrect score buf name: {buf_name}"
            return match.group()

        self.score_buf_idx = (
            get_idx(self.score_buf_name) if self.score_buf_name else None
        )
        self.mask_buf_idx = get_idx(self.mask_buf_name) if self.mask_buf_name else None
        self.kv_block_size = kv_block_size
        self.q_block_size = q_block_size
        self.has_other_buffer = has_other_buffer
        self.no_full_kv_block = no_full_kv_block
        self.other_buffer_input_offset = 2
        if self.no_full_kv_block:
            self.other_buffer_input_offset = 0
        self.fake_buffers = fake_buffers
        self.len_score_other = len_score_other
        self.len_mask_other = len_mask_other
        self.kernel_input_name_to_buffer = kernel_input_name_to_buffer
        self.block_vars = block_vars
        self.extra_sizevars = list(
            OrderedSet(
                val
                for val in self.kernel_input_name_to_buffer.values()
                if isinstance(val, sympy.Symbol)
            )
        )
        self.other_buf_start_idx = 5
        self.score_mod_other_buffers = (
            self.input_nodes[
                self.other_buf_start_idx
                + self.other_buffer_input_offset : self.other_buf_start_idx
                + self.other_buffer_input_offset
                + self.len_score_other
            ]
            if self.has_other_buffer
            else None
        )
        self.mask_mod_other_buffers = (
            self.input_nodes[
                self.other_buf_start_idx
                + self.other_buffer_input_offset
                + self.len_score_other :
            ]
            if self.has_other_buffer
            else None
        )
        self.other_ptr_data = {}