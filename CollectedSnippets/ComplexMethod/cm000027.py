def __dft(self, which):
        dft = [[x] for x in self.polyA] if which == "A" else [[x] for x in self.polyB]
        # Corner case
        if len(dft) <= 1:
            return dft[0]
        next_ncol = self.c_max_length // 2
        while next_ncol > 0:
            new_dft = [[] for i in range(next_ncol)]
            root = self.root**next_ncol

            # First half of next step
            current_root = 1
            for j in range(self.c_max_length // (next_ncol * 2)):
                for i in range(next_ncol):
                    new_dft[i].append(dft[i][j] + current_root * dft[i + next_ncol][j])
                current_root *= root
            # Second half of next step
            current_root = 1
            for j in range(self.c_max_length // (next_ncol * 2)):
                for i in range(next_ncol):
                    new_dft[i].append(dft[i][j] - current_root * dft[i + next_ncol][j])
                current_root *= root
            # Update
            dft = new_dft
            next_ncol = next_ncol // 2
        return dft[0]