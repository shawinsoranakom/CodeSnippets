def _load(self) -> None:
        if not self.file_path or not self.file_path.is_file():
            return
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if self.provider is None and self.model is None:
                self.model = data.get("model")
            if self.provider is None:
                self.provider = data.get("provider")
            self.data = data.get("data", {})
            if self.provider and self.data.get(self.provider):
                self.conversation = JsonConversation(**self.data[self.provider])
            elif not self.provider and self.data:
                self.conversation = JsonConversation(**self.data)
            self.history = data.get("items", [])
        except Exception as e:
            print(f"Error loading conversation: {e}", file=sys.stderr)