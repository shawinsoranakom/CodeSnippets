def output_markdown(
    out: TextIO,
    obj: Section | Table | list,
    base_stats: Stats,
    head_stats: Stats | None = None,
    level: int = 2,
) -> None:
    def to_markdown(x):
        if hasattr(x, "markdown"):
            return x.markdown()
        elif isinstance(x, str):
            return x
        elif x is None:
            return ""
        else:
            raise TypeError(f"Can't convert {x} to markdown")

    match obj:
        case Section():
            if obj.title:
                print("#" * level, obj.title, file=out)
                print(file=out)
                print("<details>", file=out)
                print("<summary>", obj.summary, "</summary>", file=out)
                print(file=out)
            if obj.doc:
                print(obj.doc, file=out)

            if head_stats is not None and obj.comparative is False:
                print("Not included in comparative output.\n")
            else:
                for part in obj.part_iter(base_stats, head_stats):
                    output_markdown(out, part, base_stats, head_stats, level=level + 1)
            print(file=out)
            if obj.title:
                print("</details>", file=out)
                print(file=out)

        case Table():
            header, rows = obj.get_table(base_stats, head_stats)
            if len(rows) == 0:
                return

            alignments = []
            for item in header:
                if item.endswith(":"):
                    alignments.append("right")
                else:
                    alignments.append("left")

            print("<table>", file=out)
            print("<thead>", file=out)
            print("<tr>", file=out)
            for item, align in zip(header, alignments):
                if item.endswith(":"):
                    item = item[:-1]
                print(f'<th align="{align}">{item}</th>', file=out)
            print("</tr>", file=out)
            print("</thead>", file=out)

            print("<tbody>", file=out)
            for row in rows:
                if len(row) != len(header):
                    raise ValueError(
                        "Wrong number of elements in row '" + str(row) + "'"
                    )
                print("<tr>", file=out)
                for col, align in zip(row, alignments):
                    print(f'<td align="{align}">{to_markdown(col)}</td>', file=out)
                print("</tr>", file=out)
            print("</tbody>", file=out)

            print("</table>", file=out)
            print(file=out)

        case list():
            for part in obj:
                output_markdown(out, part, base_stats, head_stats, level=level)

            print("---", file=out)
            print("Stats gathered on:", date.today(), file=out)