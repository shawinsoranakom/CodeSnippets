def validate_csv_format(file) -> bool:
    """Validate CSV file format and content"""
    try:
        content = file.read().decode('utf-8')
        dialect = csv.Sniffer().sniff(content)
        has_header = csv.Sniffer().has_header(content)
        file.seek(0)  # Reset file pointer

        if not has_header:
            return False, "CSV file must have headers"

        df = pd.read_csv(StringIO(content))
        required_columns = ['Date', 'Category', 'Amount']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        # Validate date format
        try:
            pd.to_datetime(df['Date'])
        except:
            return False, "Invalid date format in Date column"

        # Validate amount format (should be numeric after removing currency symbols)
        try:
            df['Amount'].replace('[\$,]', '', regex=True).astype(float)
        except:
            return False, "Invalid amount format in Amount column"

        return True, "CSV format is valid"
    except Exception as e:
        return False, f"Invalid CSV format: {str(e)}"