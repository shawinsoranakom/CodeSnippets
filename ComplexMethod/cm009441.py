def parse(self, chunk: str | BaseMessage) -> Iterator[AddableDict]:
        """Parse a chunk of text.

        Args:
            chunk: A chunk of text to parse. This can be a `str` or a `BaseMessage`.

        Yields:
            A `dict` representing the parsed XML element.

        Raises:
            xml.etree.ElementTree.ParseError: If the XML is not well-formed.
        """
        if isinstance(chunk, BaseMessage):
            # extract text
            chunk_content = chunk.content
            if not isinstance(chunk_content, str):
                # ignore non-string messages (e.g., function calls)
                return
            chunk = chunk_content
        # add chunk to buffer of unprocessed text
        self.buffer += chunk
        # if xml string hasn't started yet, continue to next chunk
        if not self.xml_started:
            if match := self.xml_start_re.search(self.buffer):
                # if xml string has started, remove all text before it
                self.buffer = self.buffer[match.start() :]
                self.xml_started = True
            else:
                return
        # feed buffer to parser
        self.pull_parser.feed(self.buffer)
        self.buffer = ""
        # yield all events
        try:
            events = self.pull_parser.read_events()
            for event, elem in events:  # type: ignore[misc]
                if event == "start":
                    # update current path
                    self.current_path.append(elem.tag)  # type: ignore[union-attr]
                    self.current_path_has_children = False
                elif event == "end":
                    # remove last element from current path
                    #
                    self.current_path.pop()
                    # yield element
                    if not self.current_path_has_children:
                        yield nested_element(self.current_path, elem)  # type: ignore[arg-type]
                    # prevent yielding of parent element
                    if self.current_path:
                        self.current_path_has_children = True
                    else:
                        self.xml_started = False
        except xml.etree.ElementTree.ParseError:
            # This might be junk at the end of the XML input.
            # Let's check whether the current path is empty.
            if not self.current_path:
                # If it is empty, we can ignore this error.
                return
            else:
                raise