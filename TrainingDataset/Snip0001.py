def beam_search( origin, max_iterations=1000, max_children=12 ):
    
    node_list = [ (-1,origin) ]
    current_node = Node(None)
    
    while current_node.h_score != 0:
        _,current_node = heapq.heappop( node_list )
        
        filter( 
                lambda node: heapq.heappush( node_list, node ),  
                map( heuristic, current_node.generate_children() )
            )
            
        node_list = node_list[:max_children]
    
    return current_node
