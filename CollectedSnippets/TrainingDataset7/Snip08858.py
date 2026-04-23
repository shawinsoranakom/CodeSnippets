def print_deps(node):
            out = []
            for parent in sorted(node.parents):
                out.append("%s.%s" % parent.key)
            if out:
                return " ... (%s)" % ", ".join(out)
            return ""