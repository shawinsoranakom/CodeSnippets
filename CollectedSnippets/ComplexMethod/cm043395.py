async def fetch_docs(self) -> bool:
        """Copy from local docs or download from GitHub"""
        try:
            # Try local first
            if self.local_docs.exists() and (
                any(self.local_docs.glob("*.md"))
                or any(self.local_docs.glob("*.tokens"))
            ):
                # Empty the local docs directory
                for file_path in self.docs_dir.glob("*.md"):
                    file_path.unlink()
                # for file_path in self.docs_dir.glob("*.tokens"):
                #     file_path.unlink()
                for file_path in self.local_docs.glob("*.md"):
                    shutil.copy2(file_path, self.docs_dir / file_path.name)
                # for file_path in self.local_docs.glob("*.tokens"):
                #     shutil.copy2(file_path, self.docs_dir / file_path.name)
                return True

            # Fallback to GitHub
            response = requests.get(
                "https://api.github.com/repos/unclecode/crawl4ai/contents/docs/llm.txt",
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            response.raise_for_status()

            for item in response.json():
                if item["type"] == "file" and item["name"].endswith(".md"):
                    content = requests.get(item["download_url"]).text
                    with open(self.docs_dir / item["name"], "w", encoding="utf-8") as f:
                        f.write(content)
            return True

        except Exception as e:
            self.logger.error(f"Failed to fetch docs: {str(e)}")
            raise