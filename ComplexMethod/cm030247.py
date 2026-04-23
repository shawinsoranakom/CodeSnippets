def add(self, *arg_list):
        if not arg_list:
            return self
        for item in reversed(arg_list):
            if type(self) != type(item):
                item = Stats(item)
            self.files += item.files
            self.total_calls += item.total_calls
            self.prim_calls += item.prim_calls
            self.total_tt += item.total_tt
            for func in item.top_level:
                self.top_level.add(func)

            if self.max_name_len < item.max_name_len:
                self.max_name_len = item.max_name_len

            self.fcn_list = None

            for func, stat in item.stats.items():
                if func in self.stats:
                    old_func_stat = self.stats[func]
                else:
                    old_func_stat = (0, 0, 0, 0, {},)
                self.stats[func] = add_func_stats(old_func_stat, stat)
        return self