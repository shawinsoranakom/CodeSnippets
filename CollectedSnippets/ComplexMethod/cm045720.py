def parse_cited_response(response_text, docs):
    cited_docs = [
        int(cite[1:-1]) - 1
        for cite in set(re.findall("\[\d+\]", response_text))  # noqa: W605
    ]
    start_index = response_text.find("*") + 1
    end_index = response_text.find("*", start_index)

    citations = [docs[i] for i in cited_docs if i in cited_docs]
    cleaned_citations = []

    if (
        start_index != -1 and end_index != -1
    ):  # doing this for the GIF, we need a better way to do this, TODO: redo
        cited = response_text[start_index:end_index]
        response_text = response_text[end_index:].strip()
        cited = (
            cited.replace(" ", "")
            .replace(",,", ",")
            .replace(",", ",\n")
            .replace(" ", "\n")
        )

        text_body = citations[0]["text"]
        new_text = f"<b>{cited}</b>\n\n".replace("\n\n\n", "\n") + text_body

        citations[0]["text"] = new_text

        cleaned_citations.append(citations[0])

    if len(citations) > 1:
        for doc in citations[1:]:
            text_body = doc["text"]  # TODO: unformat and clean the text
            doc["text"] = text_body
            cleaned_citations.append(doc)

    return response_text, cleaned_citations