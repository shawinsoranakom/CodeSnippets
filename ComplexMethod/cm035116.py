def handle_data(self, data):
        if self.skip:
            return

        # Only remove white space if we're not in a pre block.
        if "pre" not in self.tags:
            # remove leading and trailing whitespace in all instances
            data = remove_whitespace(data, True, True)

        if not self.paragraph:
            self.paragraph = self.doc.add_paragraph()
            self.apply_paragraph_style()

        # There can only be one nested link in a valid html document
        # You cannot have interactive content in an A tag, this includes links
        # https://html.spec.whatwg.org/#interactive-content
        link = self.tags.get("a")
        if link:
            self.handle_link(link["href"], data)
        else:
            # If there's a link, dont put the data directly in the run
            self.run = self.paragraph.add_run(data)
            spans = self.tags["span"]
            for span in spans:
                if "style" in span:
                    style = self.parse_dict_string(span["style"])
                    self.add_styles_to_run(style)

            # add font style and name
            for tag in self.tags:
                if tag in font_styles:
                    font_style = font_styles[tag]
                    setattr(self.run.font, font_style, True)

                if tag in font_names:
                    font_name = font_names[tag]
                    self.run.font.name = font_name