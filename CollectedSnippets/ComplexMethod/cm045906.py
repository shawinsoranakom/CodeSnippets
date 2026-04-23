def do_r(self, elm):
        """
        Get text from 'r' element,And try convert them to latex symbols
        @todo text style support , (sty)
        @todo \text (latex pure text support)
        """
        _str = []
        _base_str = []
        found_text = elm.findtext(f"./{OMML_NS}t")
        if found_text:
            for s in found_text:
                out_latex_str = self.process_unicode(s)
                _str.append(out_latex_str)
                _base_str.append(s)

        proc_str = escape_latex(BLANK.join(_str))
        base_proc_str = BLANK.join(_base_str)

        if "{" not in base_proc_str and "\\{" in proc_str:
            proc_str = proc_str.replace("\\{", "{")

        if "}" not in base_proc_str and "\\}" in proc_str:
            proc_str = proc_str.replace("\\}", "}")

        # Handle <m:scr> math font style (script, fraktur, double-struck, etc.)
        # OMML encodes math alphabets via <m:rPr><m:scr m:val="..."/> rather than
        # Unicode math-alphabet codepoints, so we must apply the LaTeX wrapper here.
        rPr = elm.find(f"{OMML_NS}rPr")
        if rPr is not None:
            scr_elem = rPr.find(f"{OMML_NS}scr")
            if scr_elem is not None:
                scr_val = scr_elem.get(f"{OMML_NS}val")
                latex_template = SCR_TO_LATEX.get(scr_val)
                if latex_template and proc_str.strip():
                    proc_str = latex_template.format(proc_str.strip())

        return proc_str