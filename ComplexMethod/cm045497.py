async def _create_team(
        self,
        team_config: Union[str, Path, Dict[str, Any], ComponentModel],
        input_func: Optional[InputFuncType] = None,
        env_vars: Optional[List[EnvironmentVariable]] = None,
    ) -> BaseGroupChat:
        """Create team instance from config"""
        if isinstance(team_config, (str, Path)):
            config = await self.load_from_file(team_config)
        elif isinstance(team_config, dict):
            config = team_config
        elif isinstance(team_config, ComponentModel):
            config = team_config.model_dump()
        else:
            raise ValueError(f"Unsupported team_config type: {type(team_config)}")

        # Load env vars into environment if provided
        if env_vars:
            logger.info("Loading environment variables")
            for var in env_vars:
                os.environ[var.name] = var.value

        self._team = BaseGroupChat.load_component(config)

        for agent in self._team._participants:  # type: ignore
            if hasattr(agent, "input_func") and isinstance(agent, UserProxyAgent) and input_func:
                agent.input_func = input_func

        return self._team