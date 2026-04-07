def list_formatter(item_list, tabs=1):
        indent = "\t" * tabs
        output = []
        for item, children in walk_items(item_list):
            sublist = ""
            if children:
                sublist = "\n%s<ul>\n%s\n%s</ul>\n%s" % (
                    indent,
                    list_formatter(children, tabs + 1),
                    indent,
                    indent,
                )
            output.append("%s<li>%s%s</li>" % (indent, escaper(item), sublist))
        return "\n".join(output)