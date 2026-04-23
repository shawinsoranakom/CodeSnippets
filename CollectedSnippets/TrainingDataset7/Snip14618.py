def handle_endtag(self, tag):
        if tag not in self.void_elements:
            self.output.append(f"</{tag}>")
            # Remove from the stack only if the tag matches the most recently
            # opened tag (LIFO). This avoids O(n) linear scans for unmatched
            # end tags if `deque.remove()` would be called.
            if self.tags and self.tags[0] == tag:
                self.tags.popleft()