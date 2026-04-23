def convert_decimals(obj):
            from decimal import Decimal
            import math
            if isinstance(obj, float):
                # Handle NaN and Infinity which are not valid JSON values
                if math.isnan(obj) or math.isinf(obj):
                    return None
                return obj
            if isinstance(obj, Decimal):
                return float(obj)  # 或 str(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj