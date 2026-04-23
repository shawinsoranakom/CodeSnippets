def select_recursive_step(stack, match_pos):
            path = stack.pop()
            try:
                entries = self.scandir(path)
            except OSError:
                pass
            else:
                for entry, _entry_name, entry_path in entries:
                    is_dir = False
                    try:
                        if entry.is_dir(follow_symlinks=follow_symlinks):
                            is_dir = True
                    except OSError:
                        pass

                    if is_dir or not dir_only:
                        entry_path_str = self.stringify_path(entry_path)
                        if dir_only:
                            entry_path = self.concat_path(entry_path, self.sep)
                        if match is None or match(entry_path_str, match_pos):
                            if dir_only:
                                yield from select_next(entry_path, exists=True)
                            else:
                                # Optimization: directly yield the path if this is
                                # last pattern part.
                                yield entry_path
                        if is_dir:
                            stack.append(entry_path)