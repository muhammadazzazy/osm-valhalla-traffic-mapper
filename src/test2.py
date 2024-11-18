import unittest
from graph_id import *
def binary_string(value: int, bits: int = 46) -> str:
    """Helper to format binary string with spaces between fields"""
    binary = format(value, f'0{bits}b')
    # Split into fields: 21 bits ID, 22 bits tile, 3 bits level
    return f"{binary[:-25]} {binary[-25:-3]} {binary[-3:]}"

class TestGraphId(unittest.TestCase):
    def setUp(self):
        # Known good test values from Valhalla
        self.test_values = [
            (112642252344, 0, 3015, 3357),  # (value, level, tileid, id)
            (110964530744, 0, 2968, 3311)
        ]

    def test_construction_from_value(self):
        """Test constructing GraphId from raw numeric value"""
        for value, level, tileid, id_ in self.test_values:
            gid = GraphId(value=value)
            self.assertEqual(gid.level(), level, f"Level mismatch for value {value}")
            self.assertEqual(gid.tileid(), tileid, f"Tile ID mismatch for value {value}")
            self.assertEqual(gid.graphid(), id_, f"Graph ID mismatch for value {value}")
            
            # Print detailed debug info
            print(f"\nTest value: {value}")
            print(f"Binary: {binary_string(value)}")
            print(f"Components: level={gid.level()}, tileid={gid.tileid()}, id={gid.graphid()}")

    def test_construction_from_components(self):
        """Test constructing GraphId from level, tile_id, and graph_id"""
        for value, level, tileid, id_ in self.test_values:
            gid = GraphId(tile_id=tileid, level=level, graph_id=id_)
            self.assertEqual(gid.value, value, 
                f"Value mismatch: expected {value}, got {gid.value}")
            print(f"\nConstructed from components: level={level}, tileid={tileid}, id={id_}")
            print(f"Expected value: {value}")
            print(f"Got value: {gid.value}")
            print(f"Binary: {binary_string(gid.value)}")

    def test_reconstruction(self):
        """Test that extracted components reconstruct to original value"""
        for value, _, _, _ in self.test_values:
            gid = GraphId(value=value)
            reconstructed = GraphId(
                tile_id=gid.tileid(),
                level=gid.level(),
                graph_id=gid.graphid()
            )
            self.assertEqual(gid.value, reconstructed.value,
                f"Reconstruction failed: {gid.value} != {reconstructed.value}")
            print(f"\nOriginal: {binary_string(gid.value)}")
            print(f"Reconstructed: {binary_string(reconstructed.value)}")

    def test_validation(self):
        """Test validation of component ranges"""
        invalid_cases = [
            (kMaxGraphTileId + 1, 0, 0),  # Invalid tile_id
            (0, kMaxGraphHierarchy + 1, 0),  # Invalid level
            (0, 0, kMaxGraphId + 1)  # Invalid graph_id
        ]
        for tile_id, level, graph_id in invalid_cases:
            with self.assertRaises(ValueError):
                GraphId(tile_id=tile_id, level=level, graph_id=graph_id)

    def test_bit_masks(self):
        """Test individual bit masks and shifts"""
        value = 112642252344
        gid = GraphId(value=value)
        
        # Test level mask (0x7)
        self.assertEqual(gid.value & 0x7, gid.level())
        
        # Test tile_id mask and shift
        self.assertEqual((gid.value >> 3) & 0x1FFFFF, gid.tileid())
        
        # Test graph_id mask and shift
        self.assertEqual((gid.value >> 25) & 0x1FFFFF, gid.graphid())
        
        print(f"\nBit mask tests for value: {value}")
        print(f"Binary: {binary_string(value)}")
        print(f"Level mask (0x7): {format(0x7, '03b')}")
        print(f"Tile mask (0x1FFFFF): {format(0x1FFFFF, '021b')}")
        print(f"Graph ID mask (0x1FFFFF): {format(0x1FFFFF, '021b')}")

    def test_tile_base(self):
        """Test tile_base functionality"""
        for value, level, tileid, _ in self.test_values:
            gid = GraphId(value=value)
            base = gid.tile_base()
            self.assertEqual(base.level(), level)
            self.assertEqual(base.tileid(), tileid)
            self.assertEqual(base.graphid(), 0)
            print(f"\nOriginal: {binary_string(value)}")
            print(f"Tile base: {binary_string(base.value)}")

    def test_string_representation(self):
        """Test string representation"""
        for value, level, tileid, id_ in self.test_values:
            gid = GraphId(value=value)
            expected = f"{level}/{tileid}/{id_}"
            self.assertEqual(str(gid), expected)
            print(f"\nValue: {value}")
            print(f"String representation: {str(gid)}")

if __name__ == '__main__':
    unittest.main(verbosity=2)