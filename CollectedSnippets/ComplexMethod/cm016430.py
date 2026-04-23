def finalize(self):
        """Add hidden based on selected schema options, and give outputs without ids default ids."""
        # ensure inputs, outputs, and hidden are lists
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.hidden is None:
            self.hidden = []
        # if is an api_node, will need key-related hidden
        if self.is_api_node:
            if Hidden.auth_token_comfy_org not in self.hidden:
                self.hidden.append(Hidden.auth_token_comfy_org)
            if Hidden.api_key_comfy_org not in self.hidden:
                self.hidden.append(Hidden.api_key_comfy_org)
        # if is an output_node, will need prompt and extra_pnginfo
        if self.is_output_node:
            if Hidden.prompt not in self.hidden:
                self.hidden.append(Hidden.prompt)
            if Hidden.extra_pnginfo not in self.hidden:
                self.hidden.append(Hidden.extra_pnginfo)
        # give outputs without ids default ids
        for i, output in enumerate(self.outputs):
            if output.id is None:
                output.id = f"_{i}_{output.io_type}_"