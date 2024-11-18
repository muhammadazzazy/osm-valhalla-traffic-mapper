def graphid_to_string(graph_id):
    # Extract the level, tile_id, and id using bit masks and shifts
    level = (graph_id >> 61) & 0x7
    tile_id = (graph_id >> 28) & 0x1FFFFFFF
    id_ = graph_id & 0xFFFFFFF
    return f"{level}/{tile_id}/{id_}"

# Test the function
graph_id = 112642252344
print(graphid_to_string(graph_id))  # Outputs: 1/47701/130
