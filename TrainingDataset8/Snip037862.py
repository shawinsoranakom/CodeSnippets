def save(self):
        """Save to toml file."""
        if self.activation is None:
            return

        # Create intermediate directories if necessary
        os.makedirs(os.path.dirname(self._conf_file), exist_ok=True)

        # Write the file
        data = {"email": self.activation.email}
        with open(self._conf_file, "w") as f:
            toml.dump({"general": data}, f)