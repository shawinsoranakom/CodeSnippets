def _load_team(self, team: Union[str, Path, Dict[str, Any], ComponentModel, None]) -> str:
        """
        Load team from file path, object, or create default.
        Returns the file path to the team JSON.
        Args:
            team: Can be file path (str/Path), dict, ComponentModel, or None
        """
        if team is None:
            # Create default team
            from autogenstudio.gallery.builder import create_default_lite_team

            return create_default_lite_team()

        elif isinstance(team, (str, Path)):
            # File path provided
            team_path = Path(team)
            if not team_path.exists():
                raise FileNotFoundError(f"Team file not found: {team_path}")
            return str(team_path.absolute())

        elif isinstance(team, dict):
            # Team dict provided - save to temp file
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            try:
                json.dump(team, temp_file, indent=2)
                temp_file.flush()
                return temp_file.name
            finally:
                temp_file.close()

        elif isinstance(team, ComponentModel):
            # ComponentModel - use model_dump directly
            team_dict = team.model_dump()
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            try:
                json.dump(team_dict, temp_file, indent=2)
                temp_file.flush()
                return temp_file.name
            finally:
                temp_file.close()

        else:
            # Try to serialize other team objects
            team_dict = None

            # Try dump_component() method (AutoGen teams)
            if hasattr(team, "dump_component"):
                component = team.dump_component()
                if hasattr(component, "model_dump"):
                    team_dict = component.model_dump()
                elif hasattr(component, "dict"):
                    team_dict = component.dict()
                else:
                    team_dict = dict(component)

            # Try model_dump() method (Pydantic v2)
            elif hasattr(team, "model_dump"):
                team_dict = team.model_dump()

            # Try dict() method (Pydantic v1)
            elif hasattr(team, "dict"):
                team_dict = team.dict()

            if team_dict is None:
                raise ValueError(
                    f"Cannot serialize team object of type {type(team)}. "
                    f"Expected: file path, dict, ComponentModel, or object with dump_component()/model_dump()/dict() method."
                )

            # Save serialized team to temp file
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            try:
                json.dump(team_dict, temp_file, indent=2)
                temp_file.flush()
                return temp_file.name
            finally:
                temp_file.close()