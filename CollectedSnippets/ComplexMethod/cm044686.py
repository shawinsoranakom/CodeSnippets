def get_locals(
                iter_locals: Iterable[Tuple[str, object]],
            ) -> Iterable[Tuple[str, object]]:
                """Extract locals from an iterator of key pairs."""
                if not (locals_hide_dunder or locals_hide_sunder):
                    yield from iter_locals
                    return
                for key, value in iter_locals:
                    if locals_hide_dunder and key.startswith("__"):
                        continue
                    if locals_hide_sunder and key.startswith("_"):
                        continue
                    yield key, value