def jupyter(self, arguments):
    # Dynamically install nbformat if not already installed
    nbformat = install_and_import("nbformat")
    from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

    downloads = get_downloads_path()
    current_time = datetime.now()
    formatted_time = current_time.strftime("%m-%d-%y-%I%M%p")
    filename = f"open-interpreter-{formatted_time}.ipynb"
    notebook_path = os.path.join(downloads, filename)
    nb = new_notebook()
    cells = []

    for msg in self.messages:
        if msg["role"] == "user" and msg["type"] == "message":
            # Prefix user messages with '>' to render them as block quotes, so they stand out
            content = f"> {msg['content']}"
            cells.append(new_markdown_cell(content))
        elif msg["role"] == "assistant" and msg["type"] == "message":
            cells.append(new_markdown_cell(msg["content"]))
        elif msg["type"] == "code":
            # Handle the language of the code cell
            if "format" in msg and msg["format"]:
                language = msg["format"]
            else:
                language = "python"  # Default to Python if no format specified
            code_cell = new_code_cell(msg["content"])
            code_cell.metadata.update({"language": language})
            cells.append(code_cell)

    nb["cells"] = cells

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print("")
    self.display_message(
        f"Jupyter notebook file exported to {os.path.abspath(notebook_path)}"
    )