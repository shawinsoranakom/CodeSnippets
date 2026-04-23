def _generate_dataframe(self, record_count: int) -> DataFrame:
        """Generate sample DataFrame with realistic business data.

        Args:
            record_count: Number of rows to generate

        Returns:
            DataFrame: A Langflow DataFrame with sample data
        """
        try:
            import pandas as pd

            self.log(f"pandas imported successfully, version: {pd.__version__}")
        except ImportError as e:
            self.log(f"pandas not available: {e!s}, creating simple DataFrame fallback")
            # Create a simple DataFrame-like structure without pandas
            data_result = self._generate_data(record_count)
            # Convert Data to simple DataFrame format
            try:
                # Create a basic DataFrame structure from the Data
                records = data_result.data.get("records", [])
                if records:
                    # Use first record to get column names
                    columns = list(records[0].keys()) if records else ["error"]
                    rows = [list(record.values()) for record in records]
                else:
                    columns = ["error"]
                    rows = [["pandas not available"]]

                # Create a simple dict-based DataFrame representation
                simple_df_data = {
                    col: [row[i] if i < len(row) else None for row in rows] for i, col in enumerate(columns)
                }

                # Return as DataFrame wrapper (Langflow will handle the display)
                return DataFrame(simple_df_data)
            except (ValueError, TypeError):
                # Ultimate fallback - return the Data as DataFrame
                return DataFrame({"data": [str(data_result.data)]})

        try:
            self.log(f"Starting DataFrame generation with {record_count} records")

            # Sample data for realistic business dataset
            first_names = [
                "John",
                "Jane",
                "Michael",
                "Sarah",
                "David",
                "Emily",
                "Robert",
                "Lisa",
                "William",
                "Jennifer",
            ]
            last_names = [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Garcia",
                "Miller",
                "Davis",
                "Rodriguez",
                "Martinez",
            ]
            cities = [
                "New York",
                "Los Angeles",
                "Chicago",
                "Houston",
                "Phoenix",
                "Philadelphia",
                "San Antonio",
                "San Diego",
                "Dallas",
                "San Jose",
            ]
            countries = ["USA", "Canada", "UK", "Germany", "France", "Australia", "Japan", "Brazil", "India", "Mexico"]
            products = [
                "Product A",
                "Product B",
                "Product C",
                "Product D",
                "Product E",
                "Service X",
                "Service Y",
                "Service Z",
            ]

            # Generate DataFrame data
            data = []
            base_date = datetime.now(tz=timezone.utc) - timedelta(days=365)

            self.log("Generating row data...")
            for i in range(record_count):
                row = {
                    "customer_id": f"CUST-{10000 + i}",
                    "first_name": secrets.choice(first_names),
                    "last_name": secrets.choice(last_names),
                    "email": f"user{i + 1}@example.com",
                    "age": secrets.randbelow(63) + 18,
                    "city": secrets.choice(cities),
                    "country": secrets.choice(countries),
                    "product": secrets.choice(products),
                    "order_date": (base_date + timedelta(days=secrets.randbelow(366))).strftime("%Y-%m-%d"),
                    "order_value": round(secrets.randbelow(991) + 10 + secrets.randbelow(100) / 100, 2),
                    "quantity": secrets.randbelow(10) + 1,
                    "discount": round(secrets.randbelow(31) / 100, 2),
                    "is_premium": secrets.choice([True, False]),
                    "satisfaction_score": secrets.randbelow(10) + 1,
                    "last_contact": (base_date + timedelta(days=secrets.randbelow(366))).strftime("%Y-%m-%d"),
                }
                data.append(row)
            # Create DataFrame
            self.log("Creating pandas DataFrame...")
            df = pd.DataFrame(data)
            self.log(f"DataFrame created with shape: {df.shape}")

            # Add calculated columns
            self.log("Adding calculated columns...")
            df["full_name"] = df["first_name"] + " " + df["last_name"]
            df["discounted_value"] = df["order_value"] * (1 - df["discount"])
            df["total_value"] = df["discounted_value"] * df["quantity"]

            # Age group boundaries as constants
            age_group_18_25 = 25
            age_group_26_35 = 35
            age_group_36_50 = 50
            age_group_51_65 = 65

            # Create age groups with better error handling
            try:
                df["age_group"] = pd.cut(
                    df["age"],
                    bins=[
                        0,
                        age_group_18_25,
                        age_group_26_35,
                        age_group_36_50,
                        age_group_51_65,
                        100,
                    ],
                    labels=[
                        "18-25",
                        "26-35",
                        "36-50",
                        "51-65",
                        "65+",
                    ],
                )
            except (ValueError, TypeError) as e:
                self.log(f"Error creating age groups with pd.cut: {e!s}, using simple categorization")
                df["age_group"] = df["age"].apply(
                    lambda x: "18-25"
                    if x <= age_group_18_25
                    else "26-35"
                    if x <= age_group_26_35
                    else "36-50"
                    if x <= age_group_36_50
                    else "51-65"
                    if x <= age_group_51_65
                    else "65+"
                )

            self.log(f"Successfully generated DataFrame with shape: {df.shape}, columns: {list(df.columns)}")
            # CRITICAL: Use DataFrame wrapper from Langflow
            # DO NOT set self.status when returning DataFrames - it interferes with display
            return DataFrame(df)

        except (ValueError, TypeError) as e:
            error_msg = f"Error generating DataFrame: {e!s}"
            self.log(error_msg)
            # DO NOT set self.status when returning DataFrames - it interferes with display
            # Return a fallback DataFrame with error info using Langflow wrapper
            try:
                error_df = pd.DataFrame(
                    {
                        "error": [error_msg],
                        "timestamp": [datetime.now(tz=timezone.utc).isoformat()],
                        "attempted_records": [record_count],
                    }
                )
                return DataFrame(error_df)
            except (ValueError, TypeError) as fallback_error:
                # Last resort: return simple error DataFrame
                self.log(f"Fallback also failed: {fallback_error!s}")
                simple_error_df = pd.DataFrame({"error": [error_msg]})
                return DataFrame(simple_error_df)