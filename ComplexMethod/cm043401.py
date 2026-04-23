def o(
        self, data: str, puredata: bool = False, force: Union[bool, str] = False
    ) -> None:
        """
        Deal with indentation and whitespace
        """
        if self.abbr_data is not None:
            self.abbr_data += data

        if not self.quiet:
            if self.google_doc:
                # prevent white space immediately after 'begin emphasis'
                # marks ('**' and '_')
                lstripped_data = data.lstrip()
                if self.drop_white_space and not (self.pre or self.code):
                    data = lstripped_data
                if lstripped_data != "":
                    self.drop_white_space = 0

            if puredata and not self.pre:
                # This is a very dangerous call ... it could mess up
                # all handling of &nbsp; when not handled properly
                # (see entityref)
                data = re.sub(r"\s+", r" ", data)
                if data and data[0] == " ":
                    self.space = True
                    data = data[1:]
            if not data and not force:
                return

            if self.startpre:
                # self.out(" :") #TODO: not output when already one there
                if not data.startswith("\n") and not data.startswith("\r\n"):
                    # <pre>stuff...
                    data = "\n" + data
                if self.mark_code:
                    self.out("\n[code]")
                    self.p_p = 0

            bq = ">" * self.blockquote
            if not (force and data and data[0] == ">") and self.blockquote:
                bq += " "

            if self.pre:
                if not self.list:
                    bq += "    "
                # else: list content is already partially indented
                bq += "    " * len(self.list)
                data = data.replace("\n", "\n" + bq)

            if self.startpre:
                self.startpre = False
                if self.list:
                    # use existing initial indentation
                    data = data.lstrip("\n")

            if self.start:
                self.space = False
                self.p_p = 0
                self.start = False

            if force == "end":
                # It's the end.
                self.p_p = 0
                self.out("\n")
                self.space = False

            if self.p_p:
                self.out((self.br_toggle + "\n" + bq) * self.p_p)
                self.space = False
                self.br_toggle = ""

            if self.space:
                if not self.lastWasNL:
                    self.out(" ")
                self.space = False

            if self.a and (
                (self.p_p == 2 and self.links_each_paragraph) or force == "end"
            ):
                if force == "end":
                    self.out("\n")

                newa = []
                for link in self.a:
                    if self.outcount > link.outcount:
                        self.out(
                            "   ["
                            + str(link.count)
                            + "]: "
                            + urlparse.urljoin(self.baseurl, link.attrs["href"])
                        )
                        if "title" in link.attrs and link.attrs["title"] is not None:
                            self.out(" (" + link.attrs["title"] + ")")
                        self.out("\n")
                    else:
                        newa.append(link)

                # Don't need an extra line when nothing was done.
                if self.a != newa:
                    self.out("\n")

                self.a = newa

            if self.abbr_list and force == "end":
                for abbr, definition in self.abbr_list.items():
                    self.out("  *[" + abbr + "]: " + definition + "\n")

            self.p_p = 0
            self.out(data)
            self.outcount += 1