def main():
    st.set_page_config(
        page_title="AI Financial Coach with Google ADK",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar with API key info and CSV template
    with st.sidebar:
        st.title("🔑 Setup & Templates")
        st.info("📝 Please ensure you have your Gemini API key in the .env file:\n```\nGOOGLE_API_KEY=your_api_key_here\n```")
        st.caption("This application uses Google's ADK (Agent Development Kit) and Gemini AI to provide personalized financial advice.")

        st.divider()

        # Add CSV template download
        st.subheader("📊 CSV Template")
        st.markdown("""
        Download the template CSV file with the required format:
        - Date (YYYY-MM-DD)
        - Category
        - Amount (numeric)
        """)

        # Create sample CSV content
        sample_csv = """Date,Category,Amount
2024-01-01,Housing,1200.00
2024-01-02,Food,150.50
2024-01-03,Transportation,45.00"""

        st.download_button(
            label="📥 Download CSV Template",
            data=sample_csv,
            file_name="expense_template.csv",
            mime="text/csv"
        )

    if not GEMINI_API_KEY:
        st.error("🔑 GOOGLE_API_KEY not found in environment variables. Please add it to your .env file.")
        return

    # Main content
    st.title("📊 AI Financial Coach with Google ADK")
    st.caption("Powered by Google's Agent Development Kit (ADK) and Gemini AI")
    st.info("This tool analyzes your financial data and provides tailored recommendations for budgeting, savings, and debt management using multiple specialized AI agents.")
    st.divider()

    # Create tabs for different sections
    input_tab, about_tab = st.tabs(["💼 Financial Information", "ℹ️ About"])

    with input_tab:
        st.header("Enter Your Financial Information")
        st.caption("All data is processed locally and not stored anywhere.")

        # Income and Dependants section in a container
        with st.container():
            st.subheader("💰 Income & Household")
            income_col, dependants_col = st.columns([2, 1])
            with income_col:
                monthly_income = st.number_input(
                    "Monthly Income ($)",
                    min_value=0.0,
                    step=100.0,
                    value=3000.0,
                    key="income",
                    help="Enter your total monthly income after taxes"
                )
            with dependants_col:
                dependants = st.number_input(
                    "Number of Dependants",
                    min_value=0,
                    step=1,
                    value=0,
                    key="dependants",
                    help="Include all dependants in your household"
                )

        st.divider()

        # Expenses section
        with st.container():
            st.subheader("💳 Expenses")
            expense_option = st.radio(
                "How would you like to enter your expenses?",
                ("📤 Upload CSV Transactions", "✍️ Enter Manually"),
                key="expense_option",
                horizontal=True
            )

            transaction_file = None
            manual_expenses = {}
            use_manual_expenses = False
            transactions_df = None

            if expense_option == "📤 Upload CSV Transactions":
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown("""
                    #### Upload your transaction data
                    Your CSV file should have these columns:
                    - 📅 Date (YYYY-MM-DD)
                    - 📝 Category
                    - 💲 Amount
                    """)

                    transaction_file = st.file_uploader(
                        "Choose your CSV file",
                        type=["csv"],
                        key="transaction_file",
                        help="Upload a CSV file containing your transactions"
                    )

                if transaction_file is not None:
                    # Validate CSV format
                    is_valid, message = validate_csv_format(transaction_file)

                    if is_valid:
                        try:
                            # Parse CSV content
                            transaction_file.seek(0)
                            file_content = transaction_file.read()
                            parsed_data = parse_csv_transactions(file_content)

                            # Create DataFrame
                            transactions_df = pd.DataFrame(parsed_data['transactions'])

                            # Display preview
                            display_csv_preview(transactions_df)

                            st.success("✅ Transaction file uploaded and validated successfully!")
                        except Exception as e:
                            st.error(f"❌ Error processing CSV file: {str(e)}")
                            transactions_df = None
                    else:
                        st.error(message)
                        transactions_df = None
            else:
                use_manual_expenses = True
                st.markdown("#### Enter your monthly expenses by category")

                # Define expense categories with emojis
                categories = [
                    ("🏠 Housing", "Housing"),
                    ("🔌 Utilities", "Utilities"),
                    ("🍽️ Food", "Food"),
                    ("🚗 Transportation", "Transportation"),
                    ("🏥 Healthcare", "Healthcare"),
                    ("🎭 Entertainment", "Entertainment"),
                    ("👤 Personal", "Personal"),
                    ("💰 Savings", "Savings"),
                    ("📦 Other", "Other")
                ]

                # Create three columns for better layout
                col1, col2, col3 = st.columns(3)
                cols = [col1, col2, col3]

                # Distribute categories across columns
                for i, (emoji_cat, cat) in enumerate(categories):
                    with cols[i % 3]:
                        manual_expenses[cat] = st.number_input(
                            emoji_cat,
                            min_value=0.0,
                            step=50.0,
                            value=0.0,
                            key=f"manual_{cat}",
                            help=f"Enter your monthly {cat.lower()} expenses"
                        )

                if manual_expenses and any(manual_expenses.values()):
                    st.markdown("#### 📊 Summary of Entered Expenses")
                    manual_df_disp = pd.DataFrame({
                        'Category': list(manual_expenses.keys()),
                        'Amount': list(manual_expenses.values())
                    })
                    manual_df_disp = manual_df_disp[manual_df_disp['Amount'] > 0]
                    if not manual_df_disp.empty:
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.dataframe(
                                manual_df_disp,
                                column_config={
                                    "Category": "Category",
                                    "Amount": st.column_config.NumberColumn(
                                        "Amount",
                                        format="$%.2f"
                                    )
                                },
                                hide_index=True
                            )
                        with col2:
                            st.metric(
                                "Total Monthly Expenses",
                                f"${manual_df_disp['Amount'].sum():,.2f}"
                            )

        st.divider()

        # Debt Information section
        with st.container():
            st.subheader("🏦 Debt Information")
            st.info("Enter your debts to get personalized payoff strategies using both avalanche and snowball methods.")

            num_debts = st.number_input(
                "How many debts do you have?",
                min_value=0,
                max_value=10,
                step=1,
                value=0,
                key="num_debts"
            )

            debts = []
            if num_debts > 0:
                # Create columns for debts
                cols = st.columns(min(num_debts, 3))  # Max 3 columns per row
                for i in range(num_debts):
                    col_idx = i % 3
                    with cols[col_idx]:
                        st.markdown(f"##### Debt #{i+1}")
                        debt_name = st.text_input(
                            "Name",
                            value=f"Debt {i+1}",
                            key=f"debt_name_{i}",
                            help="Enter a name for this debt (e.g., Credit Card, Student Loan)"
                        )
                        debt_amount = st.number_input(
                            "Amount ($)",
                            min_value=0.01,
                            step=100.0,
                            value=1000.0,
                            key=f"debt_amount_{i}",
                            help="Enter the current balance of this debt"
                        )
                        interest_rate = st.number_input(
                            "Interest Rate (%)",
                            min_value=0.0,
                            max_value=100.0,
                            step=0.1,
                            value=5.0,
                            key=f"debt_rate_{i}",
                            help="Enter the annual interest rate"
                        )
                        min_payment = st.number_input(
                            "Minimum Payment ($)",
                            min_value=0.0,
                            step=10.0,
                            value=50.0,
                            key=f"debt_min_payment_{i}",
                            help="Enter the minimum monthly payment required"
                        )

                        debts.append({
                            "name": debt_name,
                            "amount": debt_amount,
                            "interest_rate": interest_rate,
                            "min_payment": min_payment
                        })

                        if col_idx == 2 or i == num_debts - 1:  # Add spacing after every 3 debts or last debt
                            st.markdown("---")

        st.divider()

        # Analysis button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze_button = st.button(
                "🔄 Analyze My Finances",
                key="analyze_button",
                use_container_width=True,
                help="Click to get your personalized financial analysis"
            )

        if analyze_button:
            if expense_option == "Upload CSV Transactions" and transactions_df is None:
                st.error("Please upload a valid transaction CSV file or choose manual entry.")
                return
            if use_manual_expenses and (not manual_expenses or not any(manual_expenses.values())):
                st.warning("No manual expenses entered. Analysis might be limited.")

            st.header("Financial Analysis Results")
            with st.spinner("🤖 AI agents are analyzing your financial data..."): 
                financial_data = {
                    "monthly_income": monthly_income,
                    "dependants": dependants,
                    "transactions": transactions_df.to_dict('records') if transactions_df is not None else None,
                    "manual_expenses": manual_expenses if use_manual_expenses else None,
                    "debts": debts
                }

                finance_system = FinanceAdvisorSystem()

                try:
                    results = asyncio.run(finance_system.analyze_finances(financial_data))

                    tabs = st.tabs(["💰 Budget Analysis", "📈 Savings Strategy", "💳 Debt Reduction"])

                    with tabs[0]:
                        st.subheader("Budget Analysis")
                        if "budget_analysis" in results and results["budget_analysis"]:
                            display_budget_analysis(results["budget_analysis"])
                        else:
                            st.write("No budget analysis available.")

                    with tabs[1]:
                        st.subheader("Savings Strategy")
                        if "savings_strategy" in results and results["savings_strategy"]:
                            display_savings_strategy(results["savings_strategy"])
                        else:
                            st.write("No savings strategy available.")

                    with tabs[2]:
                        st.subheader("Debt Reduction Plan")
                        if "debt_reduction" in results and results["debt_reduction"]:
                            display_debt_reduction(results["debt_reduction"])
                        else:
                            st.write("No debt reduction plan available.")
                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")

    with about_tab:
        st.markdown("""
        ### About AI Financial Coach

        This application uses Google's Agent Development Kit (ADK) to provide comprehensive financial analysis and advice through multiple specialized AI agents:

        1. **🔍 Budget Analysis Agent**
           - Analyzes spending patterns
           - Identifies areas for cost reduction
           - Provides actionable recommendations

        2. **💰 Savings Strategy Agent**
           - Creates personalized savings plans
           - Calculates emergency fund requirements
           - Suggests automation techniques

        3. **💳 Debt Reduction Agent**
           - Develops optimal debt payoff strategies
           - Compares different repayment methods
           - Provides actionable debt reduction tips

        ### Privacy & Security

        - All data is processed locally
        - No financial information is stored or transmitted
        - Secure API communication with Google's services

        ### Need Help?

        For support or questions:
        - Check the [documentation](https://github.com/Shubhamsaboo/awesome-llm-apps)
        - Report issues on [GitHub](https://github.com/Shubhamsaboo/awesome-llm-apps/issues)
        """)