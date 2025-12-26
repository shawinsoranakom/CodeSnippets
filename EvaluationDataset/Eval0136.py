class CoordinateCompressor:

    def __init__(self, arr: list[int | float | str]) -> None:

        self.coordinate_map: dict[int | float | str, int] = {}

        self.reverse_map: list[int | float | str] = [-1] * len(arr)

        self.arr = sorted(arr)  
        self.n = len(arr) 
        self.compress_coordinates()

    def compress_coordinates(self) -> None:

        key = 0
        for val in self.arr:
            if val not in self.coordinate_map:
                self.coordinate_map[val] = key
                self.reverse_map[key] = val
                key += 1

    def compress(self, original: float | str) -> int:

        return self.coordinate_map.get(original, -1)

    def decompress(self, num: int) -> int | float | str:

        return self.reverse_map[num] if 0 <= num < len(self.reverse_map) else -1

