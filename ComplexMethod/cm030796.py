def EnumKey(self, hkey, i):
        if verbose:
            print(f"EnumKey({hkey}, {i})")
        hkey = hkey.casefold()
        if hkey not in self.open:
            raise RuntimeError("key is not open")
        prefix = f'{hkey}\\'
        subkeys = [k[len(prefix):] for k in sorted(self.keys) if k.startswith(prefix)]
        subkeys[:] = [k for k in subkeys if '\\' not in k]
        for j, n in enumerate(subkeys):
            if j == i:
                return n.removeprefix(prefix)
        raise OSError("end of enumeration")