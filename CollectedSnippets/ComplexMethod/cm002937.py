def post_process_single(self, generation: str, fix_markdown: bool = True) -> str:
        """
        Postprocess a single generated text. Regular expressions used here are taken directly from the Nougat article
        authors. These expressions are commented for clarity and tested end-to-end in most cases.

        Args:
            generation (str): The generated text to be postprocessed.
            fix_markdown (bool, optional): Whether to perform Markdown formatting fixes. Default is True.

        Returns:
            str: The postprocessed text.
        """
        generation = re.sub(
            r"(?:\n|^)#+ \d*\W? ?(.{100,})", r"\n\1", generation
        )  # too long section titles probably are none
        generation = generation.strip()
        # Remove LaTeX left margin tag
        generation = generation.replace("\n* [leftmargin=*]\n", "\n")
        # Remove lines with markdown headings starting with #, with numerals,
        # and possibly roman numerals with trailing spaces and newlines
        generation = re.sub(r"^#+ (?:[\d+\.]+|[ixv\.]+)?\s*(?:$|\n\s*)", "", generation, flags=re.MULTILINE)
        # most likely hallucinated titles
        lines = generation.split("\n")
        if lines[-1].startswith("#") and lines[-1].lstrip("#").startswith(" ") and len(lines) > 1:
            logger.info("Likely hallucinated title at the end of the page: " + lines[-1])
            generation = "\n".join(lines[:-1])
        # obvious repetition detection
        generation = truncate_repetitions(generation)
        # Reference corrections
        generation = self.remove_hallucinated_references(generation)
        # Remove lines starting with asterisks and numbers like "*[1]" and followed by capital letters and periods (ie too long references)
        generation = re.sub(r"^\* \[\d+\](\s?[A-W]\.+\s?){10,}.*$", "", generation, flags=re.MULTILINE)
        # Remove empty brackets after a reference number in brackets. *[12][]ABC will become *[12]ABC
        generation = re.sub(r"^(\* \[\d+\])\[\](.*)$", r"\1\2", generation, flags=re.MULTILINE)
        # Remove single characters before or after 2 new lines
        generation = re.sub(r"(^\w\n\n|\n\n\w$)", "", generation)
        # pmc math artifact correction
        generation = re.sub(
            r"([\s.,()])_([a-zA-Z0-9])__([a-zA-Z0-9]){1,3}_([\s.,:()])",
            r"\1\(\2_{\3}\)\4",
            generation,
        )
        generation = re.sub(r"([\s.,\d])_([a-zA-Z0-9])_([\s.,\d;])", r"\1\(\2\)\3", generation)
        # footnote mistakes
        generation = re.sub(
            r"(\nFootnote .*?:) (?:footnotetext|thanks):\W*(.*(?:\n\n|$))",
            r"\1 \2",
            generation,
        )
        # TODO Come up with footnote formatting inside a table
        generation = re.sub(r"\[FOOTNOTE:.+?\](.*?)\[ENDFOOTNOTE\]", "", generation)
        # itemize post processing
        generation = normalize_list_like_lines(generation)

        if generation.endswith((".", "}")):
            generation += "\n\n"
        if re.match(r"[A-Z0-9,;:]$", generation):
            # add space in case it there is a comma or word ending
            generation += " "
        elif generation.startswith(("#", "**", "\\begin")):
            generation = "\n\n" + generation
        elif generation.split("\n")[-1].startswith(("#", "Figure", "Table")):
            generation = generation + "\n\n"
        else:
            try:
                last_word = generation.split(" ")[-1]
                if last_word in nltk.corpus.words.words():
                    generation += " "
            except LookupError:
                # add space just in case. Will split words but better than concatenating them
                generation += " "

        # table corrections
        generation = self.correct_tables(generation)
        # Remove optional, empty square brackets after begin{array}
        generation = generation.replace("\\begin{array}[]{", "\\begin{array}{")
        # Remove empty or malformed LaTeX tabular blocks with 2 or more columns specified, with spaces and ampersands.
        generation = re.sub(
            r"\\begin{tabular}{([clr ]){2,}}\s*[& ]*\s*(\\\\)? \\end{tabular}",
            "",
            generation,
        )
        # Remove lines containing "S.A.B." one or more times. Was included in Nougat's code.
        generation = re.sub(r"(\*\*S\. A\. B\.\*\*\n+){2,}", "", generation)
        # Remove markdown-style headers that are incomplete or empty on multiple lines.
        generation = re.sub(r"^#+( [\[\d\w])?$", "", generation, flags=re.MULTILINE)
        # Remove lines with just one period.
        generation = re.sub(r"^\.\s*$", "", generation, flags=re.MULTILINE)
        # Replace instances of three or more newlines with just two newlines.
        generation = re.sub(r"\n{3,}", "\n\n", generation)
        if fix_markdown:
            return markdown_compatible(generation)
        else:
            return generation