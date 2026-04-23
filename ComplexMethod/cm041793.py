def _save(self, output_dir: Optional[str] = None, state_dict=None):
        if state_dict is None:
            state_dict = self.model.state_dict()

        if getattr(self.args, "save_safetensors", True):
            from collections import defaultdict

            ptrs = defaultdict(list)
            for name, tensor in state_dict.items():
                if isinstance(tensor, torch.Tensor):
                    ptrs[id(tensor)].append(name)

            for names in ptrs.values():
                if len(names) > 1:
                    names.sort()
                    for name in names[1:]:
                        state_dict.pop(name, None)

        super()._save(output_dir, state_dict)