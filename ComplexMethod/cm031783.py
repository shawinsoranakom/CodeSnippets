def select(self, kinds, *, include_abi_only=True, ifdef=None):
        """Yield selected items of the manifest

        kinds: set of requested kinds, e.g. {'function', 'macro'}
        include_abi_only: if True (default), include all items of the
            stable ABI.
            If False, include only items from the limited API
            (i.e. items people should use today)
        ifdef: set of feature macros (e.g. {'HAVE_FORK', 'MS_WINDOWS'}).
            If None (default), items are not filtered by this. (This is
            different from the empty set, which filters out all such
            conditional items.)
        """
        for name, item in sorted(self.contents.items()):
            if item.kind not in kinds:
                continue
            if item.abi_only and not include_abi_only:
                continue
            if (ifdef is not None
                    and item.ifdef is not None
                    and item.ifdef not in ifdef):
                continue
            yield item