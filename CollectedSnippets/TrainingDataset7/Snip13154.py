def linebreak_iter(template_source):
    yield 0
    p = template_source.find("\n")
    while p >= 0:
        yield p + 1
        p = template_source.find("\n", p + 1)
    yield len(template_source) + 1