def maybe_unwrap_docs(self, docs: pw.Json | list[pw.Json] | list[Doc]):
        if isinstance(docs, pw.Json):
            doc_ls: list[Doc] = docs.as_list()
        elif isinstance(docs, list) and all([isinstance(dc, dict) for dc in docs]):
            doc_ls = docs  # type: ignore
        elif all([isinstance(doc, pw.Json) for doc in docs]):
            doc_ls = [doc.as_dict() for doc in docs]  # type: ignore
        else:
            raise ValueError(
                """`docs` argument is not instance of (pw.Json | list[pw.Json] | list[Doc]).
                            Please check your pipeline. Using `pw.reducers.tuple` may help."""
            )

        if len(doc_ls) == 1 and isinstance(doc_ls[0], list | tuple):  # unpack if needed
            doc_ls = doc_ls[0]

        return doc_ls