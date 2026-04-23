def render_level(st: FutureCallGraph, buf: list[str], level: int) -> None:
        def add_line(line: str) -> None:
            buf.append(level * '    ' + line)

        if isinstance(st.future, tasks.Task):
            add_line(
                f'* Task(name={st.future.get_name()!r}, id={id(st.future):#x})'
            )
        else:
            add_line(
                f'* Future(id={id(st.future):#x})'
            )

        if st.call_stack:
            add_line(
                f'  + Call stack:'
            )
            for ste in st.call_stack:
                f = ste.frame

                if f.f_generator is None:
                    f = ste.frame
                    add_line(
                        f'  |   File {f.f_code.co_filename!r},'
                        f' line {f.f_lineno}, in'
                        f' {f.f_code.co_qualname}()'
                    )
                else:
                    c = f.f_generator

                    try:
                        f = c.cr_frame
                        code = c.cr_code
                        tag = 'async'
                    except AttributeError:
                        try:
                            f = c.ag_frame
                            code = c.ag_code
                            tag = 'async generator'
                        except AttributeError:
                            f = c.gi_frame
                            code = c.gi_code
                            tag = 'generator'

                    add_line(
                        f'  |   File {f.f_code.co_filename!r},'
                        f' line {f.f_lineno}, in'
                        f' {tag} {code.co_qualname}()'
                    )

        if st.awaited_by:
            add_line(
                f'  + Awaited by:'
            )
            for fut in st.awaited_by:
                render_level(fut, buf, level + 1)