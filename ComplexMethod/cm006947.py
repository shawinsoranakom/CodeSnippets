def _generate_data(self, record_count: int) -> Data:
        """Generate sample Data with JSON structure.

        Args:
            record_count: Number of records to generate

        Returns:
            Data: A Data object containing sample JSON data
        """
        # Sample data categories
        companies = [
            "TechCorp",
            "DataSystems",
            "CloudWorks",
            "InnovateLab",
            "DigitalFlow",
            "SmartSolutions",
            "FutureTech",
            "NextGen",
        ]
        departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Support", "Research"]
        statuses = ["active", "pending", "completed", "cancelled", "in_progress"]
        categories = ["A", "B", "C", "D"]

        # Generate sample records
        records = []
        base_date = datetime.now(tz=timezone.utc) - timedelta(days=365)

        for i in range(record_count):
            record = {
                "id": f"REC-{1000 + i}",
                "name": f"Sample Record {i + 1}",
                "company": secrets.choice(companies),
                "department": secrets.choice(departments),
                "status": secrets.choice(statuses),
                "category": secrets.choice(categories),
                "value": round(secrets.randbelow(9901) + 100 + secrets.randbelow(100) / 100, 2),
                "quantity": secrets.randbelow(100) + 1,
                "rating": round(secrets.randbelow(41) / 10 + 1, 1),
                "is_active": secrets.choice([True, False]),
                "created_date": (base_date + timedelta(days=secrets.randbelow(366))).isoformat(),
                "tags": [
                    secrets.choice(
                        [
                            "important",
                            "urgent",
                            "review",
                            "approved",
                            "draft",
                            "final",
                        ]
                    )
                    for _ in range(secrets.randbelow(3) + 1)
                ],
            }
            records.append(record)

        # Create the main data structure
        data_structure = {
            "records": records,
            "summary": {
                "total_count": record_count,
                "active_count": sum(1 for r in records if r["is_active"]),
                "total_value": sum(r["value"] for r in records),
                "average_rating": round(sum(r["rating"] for r in records) / record_count, 2),
                "categories": list({r["category"] for r in records}),
                "companies": list({r["company"] for r in records}),
            },
        }

        return Data(data=data_structure)