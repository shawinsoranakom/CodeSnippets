def flush_buffer():
            if string_buffer:
                self.dg.markdown(
                    " ".join(string_buffer),
                    unsafe_allow_html=unsafe_allow_html,
                )
                string_buffer[:] = []