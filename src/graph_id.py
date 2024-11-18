# Constants
kMaxGraphHierarchy = 7
kInvalidGraphId = 0x3fffffffffff  # Invalid GraphId value
kIdIncrement = 1 << 25

kMaxGraphTileId = (1 << 22) - 1  # 4,194,303
kMaxGraphId = (1 << 21) - 1  # 2,097,151

class GraphId:
    def __init__(self, tile_id=None, level=None, graph_id=None, value=None):
        """
        Initializes a GraphId instance using either a value or tile_id, level, and graph_id.
        """
        if value is not None:
            self.value = value
            self._validate()
        elif tile_id is not None and level is not None and graph_id is not None:
            if tile_id > kMaxGraphTileId:
                raise ValueError("Tile ID out of valid range")
            if level > kMaxGraphHierarchy:
                raise ValueError("Level out of valid range")
            if graph_id > kMaxGraphId:
                raise ValueError("Graph ID out of valid range")
            self.value = (level & 0x7) | ((tile_id & 0x1FFFFF) << 3) | ((graph_id & 0x1FFFFF) << 25)
        else:
            self.value = kInvalidGraphId

    @classmethod
    def invalid(cls) -> 'GraphId':
        """Returns an invalid GraphId."""
        return cls(value=kInvalidGraphId)

    def _validate(self):
        """Validates the current GraphId."""
        if self.tileid() > kMaxGraphTileId:
            raise ValueError("Tile ID out of valid range")
        if self.level() > kMaxGraphHierarchy:
            raise ValueError("Level out of valid range")
        if self.graphid() > kMaxGraphId:
            raise ValueError("Graph ID out of valid range")

    def tileid(self) -> int:
        """Returns the tile ID component of the GraphId."""
        return (self.value >> 3) & 0x1FFFFF

    def level(self) -> int:
        """Returns the level component of the GraphId."""
        return self.value & 0x7

    def graphid(self) -> int:
        """Returns the graph ID component of the GraphId."""
        return (self.value >> 25) & 0x1FFFFF

    def is_valid(self) -> bool:
        """Checks if the GraphId is valid."""
        return self.value != kInvalidGraphId

    def __repr__(self) -> str:
        """String representation of the GraphId."""
        return f"{self.level()}/{self.tileid()}/{self.graphid()}"

    def __eq__(self, other: 'GraphId') -> bool:
        """Checks if two GraphIds are equal."""
        return self.value == other.value

    def __ne__(self, other: 'GraphId') -> bool:
        """Checks if two GraphIds are not equal."""
        return self.value != other.value

    def __lt__(self, other: 'GraphId') -> bool:
        """Compares two GraphIds."""
        return self.value < other.value

    def __int__(self) -> int:
        """Returns the integer value of the GraphId."""
        return self.value

    def __hash__(self) -> int:
        """Returns a hash value for the GraphId."""
        v = self.value
        v ^= (v >> 33)
        v *= 0xff51afd7ed558ccd
        v ^= (v >> 33)
        v *= 0xc4ceb9fe1a85ec53
        v ^= (v >> 33)
        return v & ((1 << 64) - 1)  # Ensure 64-bit hash
    
    def tile_base(self) -> 'GraphId':
        """Returns a GraphId with only tileid and level."""
        return GraphId(value=(self.value & 0x1ffffff))
    
    def tile_value(self) -> int:
        """Returns a value containing level and tile id."""
        return self.value & 0x1ffffff
        
    def __add__(self, offset: int) -> 'GraphId':
        """Implements the + operator."""
        return GraphId(self.tileid(), self.level(), self.graphid() + offset)

g = GraphId(value=4362457769)
print(str(g))