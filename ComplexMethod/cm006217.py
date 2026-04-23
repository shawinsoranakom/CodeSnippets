async def select_flow_interactive(host: str, access_token: str) -> str | None:
    """Interactive flow selection."""
    flows = await list_available_flows(host, access_token)

    if not flows:
        print("❌ No starter project flows found!")
        return None

    print(f"\n{'=' * 80}")
    print("AVAILABLE STARTER PROJECT FLOWS")
    print(f"{'=' * 80}")

    for i, (flow_name, name, description) in enumerate(flows, 1):
        print(f"{i:2d}. {name}")
        print(f"    {description[:70]}{'...' if len(description) > 70 else ''}")
        print()

    while True:
        try:
            choice = input(f"Select a flow (1-{len(flows)}) or 'q' to quit: ").strip()
            if choice.lower() == "q":
                return None

            choice_num = int(choice)
            if 1 <= choice_num <= len(flows):
                selected_flow = flows[choice_num - 1]
                print(f"\n✅ Selected: {selected_flow[1]}")
                return selected_flow[0]  # Return flow name
            print(f"Please enter a number between 1 and {len(flows)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user")
            return None