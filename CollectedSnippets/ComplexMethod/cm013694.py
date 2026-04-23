def _replicatable_module(module: Module, memo: set[Module] | None = None) -> bool:
    # module.modules() contains module itself as the first element
    def descendant_modules(module: Module) -> Iterator[Module]:
        gen = module.modules()
        next(gen)
        return gen

    if not _is_jit_enabled():
        return True
    if memo is None:
        memo = set()

    # memoize visited modules
    memo.add(module)
    if _is_script_module(module):
        memo.update(descendant_modules(module))
        return all(
            _is_script_module(descendant) for descendant in descendant_modules(module)
        )

    for child in module.children():
        # since any unreplicatable module will cause the check to return
        # False early, visited modules here can be safely ignored.
        if child in memo:
            continue
        if not _replicatable_module(child, memo):
            return False

    return True