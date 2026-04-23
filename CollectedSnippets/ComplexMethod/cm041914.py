def update_chest_observation(self):
        """
        update chest_memory to chest_observation.
        Refer to @ https://github.com/MineDojo/Voyager/blob/main/voyager/agents/action.py
        """

        chests = []
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, dict) and len(chest) > 0:
                chests.append(f"{chest_position}: {chest}")
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, dict) and len(chest) == 0:
                chests.append(f"{chest_position}: Empty")
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, str):
                assert chest == "Unknown"
                chests.append(f"{chest_position}: Unknown items inside")
        assert len(chests) == len(self.chest_memory)
        if chests:
            chests = "\n".join(chests)
            self.chest_observation = f"Chests:\n{chests}\n\n"
        else:
            self.chest_observation = "Chests: None\n\n"