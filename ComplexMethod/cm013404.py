def walk(o: Any, path: str, depth: int) -> str | None:
            if depth > max_depth:
                log(f"{'  ' * depth}Depth limit at {path} ({type(o)})")
                return path + " (depth_limit)"

            key = id(o)
            if key in visited:
                return None
            visited.add(key)

            indent = "  " * depth
            log(f"{indent}Walking: {path} ({type(o)})")

            e = fail_exc(o)
            if e is None:
                log(f"{indent}✓ Pickles fine alone")
                return None
            log(f"{indent}[FAIL pickle] {type(o)} -> {e}")

            # 1) Builtin containers: walk contents directly (do NOT call __reduce_ex__)
            if isinstance(o, dict):
                for k, v in o.items():
                    bad = walk(v, f"{path}[{k!r}]", depth + 1)
                    if bad:
                        return bad
                return path

            if isinstance(o, (list, tuple)):
                for i, v in enumerate(o):
                    bad = walk(v, f"{path}[{i}]", depth + 1)
                    if bad:
                        return bad
                return path

            if isinstance(o, (set, frozenset)):
                for i, v in enumerate(o):
                    bad = walk(v, f"{path}[{i}]", depth + 1)
                    if bad:
                        return bad
                return path

            # 2) Iterator types: materialize a bounded prefix
            if hasattr(o, "__iter__") and type(o).__name__.endswith("iterator"):
                try:
                    prefix = list(itertools.islice(iter(o), max_iter_items + 1))
                except Exception:
                    prefix = None
                if prefix is not None:
                    if len(prefix) > max_iter_items:
                        log(
                            f"{indent}⚠ Iterator has more than {max_iter_items} items, "
                            f"only checking first {max_iter_items}"
                        )
                        prefix = prefix[:max_iter_items]
                    for i, v in enumerate(prefix):
                        bad = walk(v, f"{path}[{i}]", depth + 1)
                        if bad:
                            return bad
                    return path

            # 3) GraphPickler reducer_override
            try:
                red = pickler.reducer_override(o)
                log(f"{indent}reducer_override -> {type(red)}")
            except Exception as e2:
                log(f"{indent}💥 reducer_override crashed: {e2}")
                return path

            if red is not NotImplemented:
                _, args = red
                log(f"{indent}Using custom reduce, args={len(args)}")
                for i, a in enumerate(args):
                    bad = walk(a, f"{path}.reduce_args[{i}]", depth + 1)
                    if bad:
                        return bad

            # 4) Dataclasses
            if dataclasses.is_dataclass(o):
                for f in dataclasses.fields(o):
                    try:
                        v = getattr(o, f.name)
                    except Exception:
                        return f"{path}.{f.name}"
                    bad = walk(v, f"{path}.{f.name}", depth + 1)
                    if bad:
                        return bad
                return path

            # 5) __getstate__ and __dict__/__slots__
            getstate = getattr(o, "__getstate__", None)
            if callable(getstate):
                try:
                    state = getstate()
                    log(f"{indent}__getstate__ -> {type(state)}")
                except Exception as e3:
                    log(f"{indent}💥 __getstate__ failed: {e3}")
                    return path + ".__getstate__()"
                bad = walk(state, path + ".__getstate__()", depth + 1)
                if bad:
                    return bad

            if hasattr(o, "__dict__"):
                for name, v in vars(o).items():
                    bad = walk(v, f"{path}.{name}", depth + 1)
                    if bad:
                        return bad
                return path

            if hasattr(o, "__slots__"):
                for slot in o.__slots__:
                    if hasattr(o, slot):
                        bad = walk(getattr(o, slot), f"{path}.{slot}", depth + 1)
                        if bad:
                            return bad
                return path

            # 6) Last resort: reduce protocol for non-container / opaque objects
            reduce_tuple = None
            try:
                if hasattr(o, "__reduce_ex__"):
                    reduce_tuple = o.__reduce_ex__(pickle.HIGHEST_PROTOCOL)
                    log(f"{indent}__reduce_ex__ -> {type(reduce_tuple)}")
                elif hasattr(o, "__reduce__"):
                    reduce_tuple = o.__reduce__()
                    log(f"{indent}__reduce__ -> {type(reduce_tuple)}")
            except Exception as e4:
                log(f"{indent}💥 reduce protocol failed: {e4}")
                return path

            if isinstance(reduce_tuple, tuple):
                for i, part in enumerate(reduce_tuple):
                    if part is None:
                        continue
                    bad = walk(part, f"{path}.__reduce__[{i}]", depth + 1)
                    if bad:
                        return bad

            return path