def forward(self, args: list[torch.Tensor]) -> list[torch.Tensor]:
        if self.comp is None:
            self.init(args)
        comp = self.comp
        if comp is None:
            raise AssertionError("comp must not be None")
        outs = [torch.empty_like(out) for out in self.out_templates]

        if len(args) != len(self.inp_mem_fmts):
            raise AssertionError(
                f"args length {len(args)} != inp_mem_fmts length {len(self.inp_mem_fmts)}"
            )
        fixed_args = []
        for idx in range(len(args)):
            fmt = self.inp_mem_fmts[idx]
            # These constants match the values in DimOrder in serializer.py
            # TODO: See if it's possible to use those directly.
            if fmt == 0:
                fixed_args.append(args[idx].contiguous())
            elif fmt == 1:
                fixed_args.append(args[idx].permute(0, 2, 3, 1).contiguous())
            else:
                raise ValueError("Invalid mem_fmt")
        comp.run(fixed_args, outs)
        if len(outs) != len(self.out_mem_fmts):
            raise AssertionError(
                f"outs length {len(outs)} != out_mem_fmts length {len(self.out_mem_fmts)}"
            )
        for idx in range(len(self.out_templates)):
            fmt = self.out_mem_fmts[idx]
            # These constants match the values in DimOrder in serializer.py
            # TODO: See if it's possible to use those directly.
            if fmt in (0, 2):
                pass
            elif fmt == 1:
                outs[idx] = outs[idx].permute(0, 3, 1, 2)
            else:
                raise ValueError("Invalid mem_fmt")
        return outs