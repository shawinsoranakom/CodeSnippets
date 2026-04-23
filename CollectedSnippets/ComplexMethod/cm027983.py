def interactive_mode():
    """Interactive mode for creating support tickets"""
    print("=== Interactive Support Ticket Creation ===")
    print("Describe a customer issue and I'll create a structured support ticket.")
    print("Type 'quit' to exit.")
    print()

    while True:
        complaint = input("Customer Complaint: ").strip()

        if complaint.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break

        if not complaint:
            continue

        try:
            print("\nGenerating support ticket...")
            result = Runner.run_sync(support_ticket_agent, complaint)
            ticket = result.final_output

            print("\n" + "="*50)
            print("📋 SUPPORT TICKET CREATED")
            print("="*50)
            print(f"Title: {ticket.title}")
            print(f"Category: {ticket.category.value.title()}")
            print(f"Priority: {ticket.priority.value.title()}")
            if ticket.customer_name:
                print(f"Customer: {ticket.customer_name}")
            print(f"Description: {ticket.description}")
            if ticket.steps_to_reproduce:
                print("Steps to Reproduce:")
                for i, step in enumerate(ticket.steps_to_reproduce, 1):
                    print(f"  {i}. {step}")
            print(f"Estimated Resolution: {ticket.estimated_resolution_time}")
            if ticket.urgency_keywords:
                print(f"Urgency Keywords: {', '.join(ticket.urgency_keywords)}")
            print("="*50)
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()