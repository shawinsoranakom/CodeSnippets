def wrapper(f: F) -> F:
            return cache(
                func=f,
                persist=persist,
                allow_output_mutation=allow_output_mutation,
                show_spinner=show_spinner,
                suppress_st_warning=suppress_st_warning,
                hash_funcs=hash_funcs,
                max_entries=max_entries,
                ttl=ttl,
            )