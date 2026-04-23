def cache(
    func: F,
    persist: bool = False,
    allow_output_mutation: bool = False,
    show_spinner: bool = True,
    suppress_st_warning: bool = False,
    hash_funcs: Optional[HashFuncsDict] = None,
    max_entries: Optional[int] = None,
    ttl: Optional[float] = None,
) -> F:
    ...