def _convert_math_node_to_latex(self, node) -> Optional[str]:
        omath = None
        if getattr(node, "tag", None) == f"{{{OMML_NS}}}oMath":
            omath = node
        else:
            omath = node.find(".//m:oMath", namespaces=self.namespaces)

        if omath is not None:
            try:
                latex = str(oMath2Latex(omath)).strip()
            except Exception as exc:
                logger.debug(f"Failed to convert PPTX OMML equation to LaTeX: {exc}")
            else:
                if latex:
                    return latex

        fallback_text = getattr(node, "text", None)
        if isinstance(fallback_text, str):
            latex = self._strip_math_delimiters(fallback_text)
            if latex:
                return latex

        return None