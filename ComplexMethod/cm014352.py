def get_table(self, depth=None):
        if depth is None:
            depth = self.depth
        if depth is None:
            depth = 999999


        import tabulate

        tabulate.PRESERVE_WHITESPACE = True
        header = ["Module", "FLOP", "% Total"]
        values = []
        global_flops = self.get_total_flops()
        global_suffix = get_suffix_str(global_flops)
        is_global_subsumed = False

        def process_mod(mod_name, depth):
            nonlocal is_global_subsumed

            total_flops = sum(self.flop_counts[mod_name].values())

            is_global_subsumed |= total_flops >= global_flops

            padding = " " * depth
            values = []
            values.append([
                padding + mod_name,
                convert_num_with_suffix(total_flops, global_suffix),
                convert_to_percent_str(total_flops, global_flops)
            ])
            for k, v in self.flop_counts[mod_name].items():
                values.append([
                    padding + " - " + str(k),
                    convert_num_with_suffix(v, global_suffix),
                    convert_to_percent_str(v, global_flops)
                ])
            return values

        for mod in sorted(self.flop_counts.keys()):
            if mod == 'Global':
                continue
            mod_depth = mod.count(".") + 1
            if mod_depth > depth:
                continue

            cur_values = process_mod(mod, mod_depth - 1)
            values.extend(cur_values)

        # We do a bit of messing around here to only output the "Global" value
        # if there are any FLOPs in there that aren't already fully contained by
        # a module.
        if 'Global' in self.flop_counts and not is_global_subsumed:
            for value in values:
                value[0] = " " + value[0]

            values = process_mod('Global', 0) + values

        if len(values) == 0:
            values = [["Global", "0", "0%"]]

        return tabulate.tabulate(values, headers=header, colalign=("left", "right", "right"))