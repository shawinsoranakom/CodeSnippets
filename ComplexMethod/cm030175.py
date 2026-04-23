def _help_message_from_doc(self, doc, usage_only=False):
        lines = [line.strip() for line in doc.rstrip().splitlines()]
        if not lines:
            return "No help message found."
        if "" in lines:
            usage_end = lines.index("")
        else:
            usage_end = 1
        formatted = []
        indent = " " * len(self.prompt)
        for i, line in enumerate(lines):
            if i == 0:
                prefix = "Usage: "
            elif i < usage_end:
                prefix = "       "
            else:
                if usage_only:
                    break
                prefix = ""
            formatted.append(indent + prefix + line)
        return "\n".join(formatted)