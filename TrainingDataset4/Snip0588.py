async def get_available_blocks(self) -> List[Dict[str, Any]]:
        """Get available agent blocks from database."""
        print("Getting available agent blocks...")

        # Get blocks from database instead of the registry
        db_blocks = await prisma.agentblock.find_many()
        if not db_blocks:
            print("No blocks found in database, creating some basic blocks...")
            # Create some basic blocks if none exist
            from backend.blocks.io import AgentInputBlock, AgentOutputBlock
            from backend.blocks.maths import CalculatorBlock
            from backend.blocks.time_blocks import GetCurrentTimeBlock

            blocks_to_create = [
                AgentInputBlock(),
                AgentOutputBlock(),
                CalculatorBlock(),
                GetCurrentTimeBlock(),
            ]

            for block in blocks_to_create:
                try:
                    await prisma.agentblock.create(
                        data={
                            "id": block.id,
                            "name": block.name,
                            "inputSchema": "{}",
                            "outputSchema": "{}",
                        }
                    )
                except Exception as e:
                    print(f"Error creating block {block.name}: {e}")

            # Get blocks again after creation
            db_blocks = await prisma.agentblock.find_many()

        self.agent_blocks = [
            {"id": block.id, "name": block.name} for block in db_blocks
        ]
        print(f"Found {len(self.agent_blocks)} blocks in database")
        return self.agent_blocks
