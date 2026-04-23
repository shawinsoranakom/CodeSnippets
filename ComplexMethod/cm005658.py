def create_loading_report(self) -> str | None:
        """Generate the minimal table of a loading report."""
        term_w = _get_terminal_width()

        rows = []
        tips = "\n\nNotes:"
        if self.unexpected_keys:
            tips += f"\n- {_style('UNEXPECTED:', 'orange')}\t" + _style(
                "can be ignored when loading from different task/architecture; not ok if you expect identical arch.",
                "italic",
            )
            for k in update_key_name(self.unexpected_keys):
                status = _style("UNEXPECTED", "orange")
                rows.append([k, status, "", ""])

        if self.missing_keys:
            tips += f"\n- {_style('MISSING:', 'red')}\t" + _style(
                "those params were newly initialized because missing from the checkpoint. Consider training on your downstream task.",
                "italic",
            )
            for k in update_key_name(self.missing_keys):
                status = _style("MISSING", "red")
                rows.append([k, status, ""])

        if self.mismatched_keys:
            tips += f"\n- {_style('MISMATCH:', 'yellow')}\t" + _style(
                "ckpt weights were loaded, but they did not match the original empty weight shapes.", "italic"
            )
            iterator = {a: (b, c) for a, b, c in self.mismatched_keys}
            for key, (shape_ckpt, shape_model) in update_key_name(iterator).items():
                status = _style("MISMATCH", "yellow")
                data = [
                    key,
                    status,
                    f"Reinit due to size mismatch - ckpt: {str(shape_ckpt)} vs model:{str(shape_model)}",
                ]
                rows.append(data)

        if self.conversion_errors:
            tips += f"\n- {_style('CONVERSION:', 'purple')}\t" + _style(
                "originate from the conversion scheme", "italic"
            )
            for k, v in update_key_name(self.conversion_errors).items():
                status = _style("CONVERSION", "purple")
                _details = f"\n\n{v}\n\n"
                rows.append([k, status, _details])

        # If nothing is wrong, return None
        if len(rows) == 0:
            return None

        headers = ["Key", "Status"]
        if term_w > 200:
            headers += ["Details"]
        else:
            headers += ["", ""]
        table = _make_table(rows, headers=headers)
        report = table + tips

        return report