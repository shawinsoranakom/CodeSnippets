def generate(self, sections: List[str], mode: str = "extended") -> str:
        # Get all markdown files
        all_files = glob.glob(str(self.docs_dir / "[0-9]*.md")) + glob.glob(
            str(self.docs_dir / "[0-9]*.xs.md")
        )

        # Extract base names without extensions
        base_docs = {
            Path(f).name.split(".")[0]
            for f in all_files
            if not Path(f).name.endswith(".q.md")
        }

        # Filter by sections if provided
        if sections:
            base_docs = {
                doc
                for doc in base_docs
                if any(section.lower() in doc.lower() for section in sections)
            }

        # Get file paths based on mode
        files = []
        for doc in sorted(
            base_docs,
            key=lambda x: int(x.split("_")[0]) if x.split("_")[0].isdigit() else 999999,
        ):
            if mode == "condensed":
                xs_file = self.docs_dir / f"{doc}.xs.md"
                regular_file = self.docs_dir / f"{doc}.md"
                files.append(str(xs_file if xs_file.exists() else regular_file))
            else:
                files.append(str(self.docs_dir / f"{doc}.md"))

        # Read and format content
        content = []
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    fname = Path(file).name
                    content.append(f"{'#'*20}\n# {fname}\n{'#'*20}\n\n{f.read()}")
            except Exception as e:
                self.logger.error(f"Error reading {file}: {str(e)}")

        return "\n\n---\n\n".join(content) if content else ""