def handle_tag(self, tag, attrs, start):
        # Handle <base> tag to update base URL for relative links
        # Must be handled before preserved tags since <base> is in <head>
        if tag == "base" and start:
            href = attrs.get("href") if attrs else None
            if href:
                self.baseurl = href
            # Also let parent class handle it
            return super().handle_tag(tag, attrs, start)

        # Handle preserved tags
        if tag in self.preserve_tags:
            if start:
                if self.preserve_depth == 0:
                    self.current_preserved_tag = tag
                    self.preserved_content = []
                    # Format opening tag with attributes
                    attr_str = "".join(
                        f' {k}="{v}"' for k, v in attrs.items() if v is not None
                    )
                    self.preserved_content.append(f"<{tag}{attr_str}>")
                self.preserve_depth += 1
                return
            else:
                self.preserve_depth -= 1
                if self.preserve_depth == 0:
                    self.preserved_content.append(f"</{tag}>")
                    # Output the preserved HTML block with proper spacing
                    preserved_html = "".join(self.preserved_content)
                    self.o("\n" + preserved_html + "\n")
                    self.current_preserved_tag = None
                return

        # If we're inside a preserved tag, collect all content
        if self.preserve_depth > 0:
            if start:
                # Format nested tags with attributes
                attr_str = "".join(
                    f' {k}="{v}"' for k, v in attrs.items() if v is not None
                )
                self.preserved_content.append(f"<{tag}{attr_str}>")
            else:
                self.preserved_content.append(f"</{tag}>")
            return

        # Handle pre tags
        if tag == "pre":
            if start:
                self.o("\n```\n")  # Markdown code block start
                self.inside_pre = True
            else:
                self.o("\n```\n")  # Markdown code block end
                self.inside_pre = False
        elif tag == "code":
            if self.inside_pre and not self.handle_code_in_pre:
                # Ignore code tags inside pre blocks if handle_code_in_pre is False
                return
            if start:
                if not self.inside_link:
                    self.o("`")  # Only output backtick if not inside a link
                self.inside_code = True
            else:
                if not self.inside_link:
                    self.o("`")  # Only output backtick if not inside a link
                self.inside_code = False

            # If inside a link, let the parent class handle the content
            if self.inside_link:
                super().handle_tag(tag, attrs, start) 
        else:
            super().handle_tag(tag, attrs, start)