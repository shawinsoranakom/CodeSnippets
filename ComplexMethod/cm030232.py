def phase2(self): # Distinguish files, directories, funnies
        self.common_dirs = []
        self.common_files = []
        self.common_funny = []

        for x in self.common:
            a_path = os.path.join(self.left, x)
            b_path = os.path.join(self.right, x)

            ok = True
            try:
                a_stat = os.stat(a_path)
            except (OSError, ValueError):
                # See https://github.com/python/cpython/issues/122400
                # for the rationale for protecting against ValueError.
                # print('Can\'t stat', a_path, ':', why.args[1])
                ok = False
            try:
                b_stat = os.stat(b_path)
            except (OSError, ValueError):
                # print('Can\'t stat', b_path, ':', why.args[1])
                ok = False

            if ok:
                a_type = stat.S_IFMT(a_stat.st_mode)
                b_type = stat.S_IFMT(b_stat.st_mode)
                if a_type != b_type:
                    self.common_funny.append(x)
                elif stat.S_ISDIR(a_type):
                    self.common_dirs.append(x)
                elif stat.S_ISREG(a_type):
                    self.common_files.append(x)
                else:
                    self.common_funny.append(x)
            else:
                self.common_funny.append(x)