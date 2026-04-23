def __iter__(self):
        # Iterate over this file-like object by newlines
        buffer_ = []
        for chunk in self.chunks():
            for line in chunk.splitlines(True):
                if buffer_:
                    if endswith_cr(buffer_[-1]) and not equals_lf(line):
                        # Line split after a \r newline; yield buffer_.
                        yield type(buffer_[0])().join(buffer_)
                        # Continue with line.
                        buffer_ = []
                    else:
                        # Line either split without a newline (line
                        # continues after buffer_) or with \r\n
                        # newline (line == b'\n').
                        buffer_.append(line)

                if not buffer_:
                    # If this is the end of a \n or \r\n line, yield.
                    if endswith_lf(line):
                        yield line
                    else:
                        buffer_.append(line)
                elif endswith_lf(line):
                    yield type(buffer_[0])().join(buffer_)
                    buffer_ = []

        if buffer_:
            yield type(buffer_[0])().join(buffer_)