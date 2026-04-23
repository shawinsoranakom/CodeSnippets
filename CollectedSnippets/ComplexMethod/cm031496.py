def recolorize_main(self):
        "Evaluate text and apply colorizing tags."
        next = "1.0"
        while todo_tag_range := self.tag_nextrange("TODO", next):
            self.tag_remove("SYNC", todo_tag_range[0], todo_tag_range[1])
            sync_tag_range = self.tag_prevrange("SYNC", todo_tag_range[0])
            head = sync_tag_range[1] if sync_tag_range else "1.0"

            chars = ""
            next = head
            lines_to_get = 1
            ok = False
            while not ok:
                mark = next
                next = self.index(mark + "+%d lines linestart" %
                                         lines_to_get)
                lines_to_get = min(lines_to_get * 2, 100)
                ok = "SYNC" in self.tag_names(next + "-1c")
                line = self.get(mark, next)
                ##print head, "get", mark, next, "->", repr(line)
                if not line:
                    return
                for tag in self.tagdefs:
                    self.tag_remove(tag, mark, next)
                chars += line
                self._add_tags_in_section(chars, head)
                if "SYNC" in self.tag_names(next + "-1c"):
                    head = next
                    chars = ""
                else:
                    ok = False
                if not ok:
                    # We're in an inconsistent state, and the call to
                    # update may tell us to stop.  It may also change
                    # the correct value for "next" (since this is a
                    # line.col string, not a true mark).  So leave a
                    # crumb telling the next invocation to resume here
                    # in case update tells us to leave.
                    self.tag_add("TODO", next)
                self.update_idletasks()
                if self.stop_colorizing:
                    if DEBUG: print("colorizing stopped")
                    return