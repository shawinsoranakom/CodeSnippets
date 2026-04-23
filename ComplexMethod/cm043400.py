def handle_tag(
        self, tag: str, attrs: Dict[str, Optional[str]], start: bool
    ) -> None:
        self.current_tag = tag

        if self.tag_callback is not None:
            if self.tag_callback(self, tag, attrs, start) is True:
                return

        # Handle <base> tag to update base URL for relative links
        if tag == "base" and start:
            href = attrs.get("href")
            if href:
                self.baseurl = href

        # first thing inside the anchor tag is another tag
        # that produces some output
        if (
            start
            and self.maybe_automatic_link is not None
            and tag not in ["p", "div", "style", "dl", "dt"]
            and (tag != "img" or self.ignore_images)
        ):
            self.o("[")
            self.maybe_automatic_link = None
            self.empty_link = False

        if self.google_doc:
            # the attrs parameter is empty for a closing tag. in addition, we
            # need the attributes of the parent nodes in order to get a
            # complete style description for the current element. we assume
            # that google docs export well formed html.
            parent_style: Dict[str, str] = {}
            if start:
                if self.tag_stack:
                    parent_style = self.tag_stack[-1][2]
                tag_style = element_style(attrs, self.style_def, parent_style)
                self.tag_stack.append((tag, attrs, tag_style))
            else:
                dummy, attrs, tag_style = (
                    self.tag_stack.pop() if self.tag_stack else (None, {}, {})
                )
                if self.tag_stack:
                    parent_style = self.tag_stack[-1][2]

        if hn(tag):
            # check if nh is inside of an 'a' tag (incorrect but found in the wild)
            if self.astack:
                if start:
                    self.inheader = True
                    # are inside link name, so only add '#' if it can appear before '['
                    if self.outtextlist and self.outtextlist[-1] == "[":
                        self.outtextlist.pop()
                        self.space = False
                        self.o(hn(tag) * "#" + " ")
                        self.o("[")
                else:
                    self.p_p = 0  # don't break up link name
                    self.inheader = False
                    return  # prevent redundant emphasis marks on headers
            else:
                self.p()
                if start:
                    self.inheader = True
                    self.o(hn(tag) * "#" + " ")
                else:
                    self.inheader = False
                    return  # prevent redundant emphasis marks on headers

        if tag in ["p", "div"]:
            if self.google_doc:
                if start and google_has_height(tag_style):
                    self.p()
                else:
                    self.soft_br()
            elif self.astack:
                pass
            elif self.split_next_td:
                pass
            else:
                self.p()

        if tag == "br" and start:
            if self.blockquote > 0:
                self.o("  \n> ")
            else:
                self.o("  \n")

        if tag == "hr" and start:
            self.p()
            self.o("* * *")
            self.p()

        if tag in ["head", "style", "script"]:
            if start:
                self.quiet += 1
            else:
                self.quiet -= 1

        if tag == "style":
            if start:
                self.style += 1
            else:
                self.style -= 1

        if tag in ["body"]:
            self.quiet = 0  # sites like 9rules.com never close <head>

        if tag == "blockquote":
            if start:
                self.p()
                self.o("> ", force=True)
                self.start = True
                self.blockquote += 1
            else:
                self.blockquote -= 1
                self.p()

        if tag in ["em", "i", "u"] and not self.ignore_emphasis:
            # Separate with a space if we immediately follow an alphanumeric
            # character, since otherwise Markdown won't render the emphasis
            # marks, and we'll be left with eg 'foo_bar_' visible.
            # (Don't add a space otherwise, though, since there isn't one in the
            # original HTML.)
            if (
                start
                and self.preceding_data
                and self.preceding_data[-1] not in string.whitespace
                and self.preceding_data[-1] not in string.punctuation
            ):
                emphasis = " " + self.emphasis_mark
                self.preceding_data += " "
            else:
                emphasis = self.emphasis_mark

            self.o(emphasis)
            if start:
                self.stressed = True

        if tag in ["strong", "b"] and not self.ignore_emphasis:
            # Separate with space if we immediately follow an * character, since
            # without it, Markdown won't render the resulting *** correctly.
            # (Don't add a space otherwise, though, since there isn't one in the
            # original HTML.)
            if (
                start
                and self.preceding_data
                # When `self.strong_mark` is set to empty, the next condition
                # will cause IndexError since it's trying to match the data
                # with the first character of the `self.strong_mark`.
                and len(self.strong_mark) > 0
                and self.preceding_data[-1] == self.strong_mark[0]
            ):
                strong = " " + self.strong_mark
                self.preceding_data += " "
            else:
                strong = self.strong_mark

            self.o(strong)
            if start:
                self.stressed = True

        if tag in ["del", "strike", "s"]:
            if start and self.preceding_data and self.preceding_data[-1] == "~":
                strike = " ~~"
                self.preceding_data += " "
            else:
                strike = "~~"

            self.o(strike)
            if start:
                self.stressed = True

        if self.google_doc:
            if not self.inheader:
                # handle some font attributes, but leave headers clean
                self.handle_emphasis(start, tag_style, parent_style)

        if tag in ["kbd", "code", "tt"] and not self.pre:
            self.o("`")  # TODO: `` `this` ``
            self.code = not self.code

        if tag == "abbr":
            if start:
                self.abbr_title = None
                self.abbr_data = ""
                if "title" in attrs:
                    self.abbr_title = attrs["title"]
            else:
                if self.abbr_title is not None:
                    assert self.abbr_data is not None
                    self.abbr_list[self.abbr_data] = self.abbr_title
                    self.abbr_title = None
                self.abbr_data = None

        if tag == "q":
            if not self.quote:
                self.o(self.open_quote)
            else:
                self.o(self.close_quote)
            self.quote = not self.quote

        def link_url(self: HTML2Text, link: str, title: str = "") -> None:
            url = urlparse.urljoin(self.baseurl, link)
            title = ' "{}"'.format(title) if title.strip() else ""
            self.o("]({url}{title})".format(url=escape_md(url), title=title))

        if tag == "a" and not self.ignore_links:
            if start:
                self.inside_link = True
                if (
                    "href" in attrs
                    and attrs["href"] is not None
                    and not (self.skip_internal_links and attrs["href"].startswith("#"))
                    and not (
                        self.ignore_mailto_links and attrs["href"].startswith("mailto:")
                    )
                ):
                    self.astack.append(attrs)
                    self.maybe_automatic_link = attrs["href"]
                    self.empty_link = True
                    if self.protect_links:
                        attrs["href"] = "<" + attrs["href"] + ">"
                else:
                    self.astack.append(None)
            else:
                self.inside_link = False
                if self.astack:
                    a = self.astack.pop()
                    if self.maybe_automatic_link and not self.empty_link:
                        self.maybe_automatic_link = None
                    elif a:
                        assert a["href"] is not None
                        if self.empty_link:
                            self.o("[")
                            self.empty_link = False
                            self.maybe_automatic_link = None
                        if self.inline_links:
                            self.p_p = 0
                            title = a.get("title") or ""
                            title = escape_md(title)
                            link_url(self, a["href"], title)
                        else:
                            i = self.previousIndex(a)
                            if i is not None:
                                a_props = self.a[i]
                            else:
                                self.acount += 1
                                a_props = AnchorElement(a, self.acount, self.outcount)
                                self.a.append(a_props)
                            self.o("][" + str(a_props.count) + "]")

        if tag == "img" and start and not self.ignore_images:
            if "src" in attrs and attrs["src"] is not None:
                if not self.images_to_alt:
                    attrs["href"] = attrs["src"]
                alt = attrs.get("alt") or self.default_image_alt

                # If we have images_with_size, write raw html including width,
                # height, and alt attributes
                if self.images_as_html or (
                    self.images_with_size and ("width" in attrs or "height" in attrs)
                ):
                    self.o("<img src='" + attrs["src"] + "' ")
                    if "width" in attrs and attrs["width"] is not None:
                        self.o("width='" + attrs["width"] + "' ")
                    if "height" in attrs and attrs["height"] is not None:
                        self.o("height='" + attrs["height"] + "' ")
                    if alt:
                        self.o("alt='" + alt + "' ")
                    self.o("/>")
                    return

                # If we have a link to create, output the start
                if self.maybe_automatic_link is not None:
                    href = self.maybe_automatic_link
                    if (
                        self.images_to_alt
                        and escape_md(alt) == href
                        and self.absolute_url_matcher.match(href)
                    ):
                        self.o("<" + escape_md(alt) + ">")
                        self.empty_link = False
                        return
                    else:
                        self.o("[")
                        self.maybe_automatic_link = None
                        self.empty_link = False

                # If we have images_to_alt, we discard the image itself,
                # considering only the alt text.
                if self.images_to_alt:
                    self.o(escape_md(alt))
                else:
                    self.o("![" + escape_md(alt) + "]")
                    if self.inline_links:
                        href = attrs.get("href") or ""
                        self.o(
                            "(" + escape_md(urlparse.urljoin(self.baseurl, href)) + ")"
                        )
                    else:
                        i = self.previousIndex(attrs)
                        if i is not None:
                            a_props = self.a[i]
                        else:
                            self.acount += 1
                            a_props = AnchorElement(attrs, self.acount, self.outcount)
                            self.a.append(a_props)
                        self.o("[" + str(a_props.count) + "]")

        if tag == "dl" and start:
            self.p()  # Add paragraph break before list starts
            self.p_p = 0  # Reset paragraph state

        elif tag == "dt" and start:
            if self.p_p == 0:  # If not first term
                self.o("\n\n")  # Add spacing before new term-definition pair
            self.p_p = 0  # Reset paragraph state

        elif tag == "dt" and not start:
            self.o("\n")  # Single newline between term and definition

        elif tag == "dd" and start:
            self.o("    ")  # Indent definition

        elif tag == "dd" and not start:
            self.p_p = 0

        if tag in ["ol", "ul"]:
            # Google Docs create sub lists as top level lists
            if not self.list and not self.lastWasList:
                self.p()
            if start:
                if self.google_doc:
                    list_style = google_list_style(tag_style)
                else:
                    list_style = tag
                numbering_start = list_numbering_start(attrs)
                self.list.append(ListElement(list_style, numbering_start))
            else:
                if self.list:
                    self.list.pop()
                    if not self.google_doc and not self.list:
                        self.o("\n")
            self.lastWasList = True
        else:
            self.lastWasList = False

        if tag == "li":
            self.pbr()
            if start:
                if self.list:
                    li = self.list[-1]
                else:
                    li = ListElement("ul", 0)
                if self.google_doc:
                    self.o("  " * self.google_nest_count(tag_style))
                else:
                    # Indent two spaces per list, except use three spaces for an
                    # unordered list inside an ordered list.
                    # https://spec.commonmark.org/0.28/#motivation
                    # TODO: line up <ol><li>s > 9 correctly.
                    parent_list = None
                    for list in self.list:
                        self.o(
                            "   " if parent_list == "ol" and list.name == "ul" else "  "
                        )
                        parent_list = list.name

                if li.name == "ul":
                    self.o(self.ul_item_mark + " ")
                elif li.name == "ol":
                    li.num += 1
                    self.o(str(li.num) + ". ")
                self.start = True

        if tag == "caption":
            if not start:
                # Ensure caption text ends on its own line before table rows
                self.soft_br()

        if tag in ["table", "tr", "td", "th"]:
            if self.ignore_tables:
                if tag == "tr":
                    if start:
                        pass
                    else:
                        self.soft_br()
                else:
                    pass

            elif self.bypass_tables:
                if start:
                    self.soft_br()
                if tag in ["td", "th"]:
                    if start:
                        self.o("<{}>\n\n".format(tag))
                    else:
                        self.o("\n</{}>".format(tag))
                else:
                    if start:
                        self.o("<{}>".format(tag))
                    else:
                        self.o("</{}>".format(tag))

            else:
                if tag == "table":
                    if start:
                        self.table_start = True
                        if self.pad_tables:
                            self.o("<" + config.TABLE_MARKER_FOR_PAD + ">")
                            self.o("  \n")
                        else:
                            # Ensure table starts on its own line (GFM requirement)
                            self.soft_br()
                    else:
                        if self.pad_tables:
                            # add break in case the table is empty or its 1 row table
                            self.soft_br()
                            self.o("</" + config.TABLE_MARKER_FOR_PAD + ">")
                            self.o("  \n")
                if tag in ["td", "th"] and start:
                    if self.pad_tables:
                        # pad_tables mode: keep upstream inter-cell delimiter only
                        # (pad post-processor adds leading/trailing pipes and alignment)
                        if self.split_next_td:
                            self.o("| ")
                    else:
                        # GFM mode: leading pipe on first cell, spaced pipes between cells
                        if self.split_next_td:
                            self.o(" | ")
                        else:
                            self.o("| ")
                    self.split_next_td = True

                if tag == "tr" and start:
                    self.td_count = 0
                if tag == "tr" and not start:
                    if not self.pad_tables:
                        # Add trailing pipe for GFM compliance
                        self.o(" |")
                    self.split_next_td = False
                    self.soft_br()
                if tag == "tr" and not start and self.table_start:
                    if self.pad_tables:
                        # pad_tables: plain separator (post-processor reformats)
                        self.o("|".join(["---"] * self.td_count))
                    else:
                        # GFM: separator with leading/trailing pipes
                        self.o("| " + " | ".join(["---"] * self.td_count) + " |")
                    self.soft_br()
                    self.table_start = False
                if tag in ["td", "th"] and start:
                    self.td_count += 1

        if tag == "pre":
            if start:
                self.startpre = True
                self.pre = True
            else:
                self.pre = False
                if self.mark_code:
                    self.out("\n[/code]")
            self.p()

        if tag in ["sup", "sub"] and self.include_sup_sub:
            if start:
                self.o("<{}>".format(tag))
            else:
                self.o("</{}>".format(tag))