def forward(self, hidden_state, output_hidden_states=False, return_dict=True):
        all_hidden_states = () if output_hidden_states else None

        for stage in self.stages:
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_state,)
            hidden_state = stage(hidden_state)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_state,)
        if not return_dict:
            return tuple(v for v in [hidden_state, all_hidden_states] if v is not None)

        return BaseModelOutputWithNoAttention(last_hidden_state=hidden_state, hidden_states=all_hidden_states)