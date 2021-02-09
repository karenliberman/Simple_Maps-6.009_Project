#!/usr/bin/env python3

from util import read_osm_data, great_circle_distance, to_local_kml_url

# NO ADDITIONAL IMPORTS!


ALLOWED_HIGHWAY_TYPES = {
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'unclassified',
    'residential', 'living_street', 'motorway_link', 'trunk_link',
    'primary_link', 'secondary_link', 'tertiary_link',
}


DEFAULT_SPEED_LIMIT_MPH = {
    'motorway': 60,
    'trunk': 45,
    'primary': 35,
    'secondary': 30,
    'residential': 25,
    'tertiary': 25,
    'unclassified': 25,
    'living_street': 10,
    'motorway_link': 30,
    'trunk_link': 30,
    'primary_link': 30,
    'secondary_link': 30,
    'tertiary_link': 25,
}


def build_auxiliary_structures(nodes_filename, ways_filename):
    """
    Create any auxiliary structures you are interested in, by reading the data
    from the given filenames (using read_osm_data)
    
    Nodes will become a dictionary: the key is the ID and the 
    value is a tuple with latitude and longitude coordinates
    
    Ways will only be added if they have one of the ok highway types - 
    Ways will become a dictionary: the key is the ID and the value
    is tuple 
    """
    newNodes = {}
    newWays = {}
    
    
    for ways in read_osm_data(ways_filename):
        #only adds the way if it is an allowed type
        if 'highway' in ways['tags']:
            if ways['tags']['highway'] in ALLOWED_HIGHWAY_TYPES:
                
                for i in range(len(ways['nodes'])):
                    #each node gets its own dictionary key if it has not been added yet
                    if ways['nodes'][i] not in newWays:
                        newWays[ways['nodes'][i]] = set()
                    
                    #adds as values to the respective key that has a way to their location
                    if i>0 and (('oneway' not in ways['tags']) or (ways['tags']['oneway'] != 'yes')):
                        if 'maxspeed_mph' in ways['tags']:
                            newWays[ways['nodes'][i]].add((ways['nodes'][i-1], ways['tags']['highway'], ways['tags']['maxspeed_mph']))
                        else:
                            newWays[ways['nodes'][i]].add((ways['nodes'][i-1], ways['tags']['highway'], 0))

                    if (i< ( len(ways['nodes']) -1)):
                        if 'maxspeed_mph' in ways['tags']:
                            newWays[ways['nodes'][i]].add((ways['nodes'][i+1], ways['tags']['highway'], ways['tags']['maxspeed_mph'])) 
                        else:
                            newWays[ways['nodes'][i]].add((ways['nodes'][i+1], ways['tags']['highway'], 0))
                #sometimes two different nodes are considereced connecting if they have different highway types
    
    #makes the nodes correspond to a lat, lon location
    for node in read_osm_data(nodes_filename):
        if node['id'] in newWays:

            newNodes[node['id']] = (node['lat'], node['lon'])
                            
    
    return (newNodes, newWays)

def add_to_agenda(nodes, agenda, pathToAdd, destination):
    '''
    Parameters
    ----------
    agenda : (set) is a set full of tuples, each tuple with 3 elements: the first element
    is a list with a path to be considered, second is the calculated length of that path and the third is 
    the predicted length from the end of that path to the destination
    pathToAdd : a tuple: the first element being the path that needs to be added and the second is the 
    calculated length of that path before the last node on that path was added
    destination : the final node ID they that we are trying to reach

    Returns
    -------
    The new agenda version

    '''
    path = pathToAdd[0]
    
    #calculates the distance from the previous node to that node
    lastStretch = great_circle_distance(nodes[path[len(path)-1]], nodes[path[len(path)-2]])

    calculatedDistance = pathToAdd[1] + lastStretch
    #estimates the distance from that node to the final destination
    estimated = great_circle_distance(nodes[path[len(path)-1]], nodes[destination])

    agenda.add((path, calculatedDistance, estimated))
    
    return agenda
    
    
    
def find_short_path_nodes(aux_structures, node1, node2):
    """
    Return the shortest path between the two nodes

    Parameters:
        aux_structures: the result of calling build_auxiliary_structures
        node1: node representing the start location
        node2: node representing the end location

    Returns:
        a list of node IDs representing the shortest path (in terms of
        distance) from node1 to node2
    """
    nodesCords = aux_structures[0]
    ways = aux_structures[1]
    agenda = set()
    expanded = set()
    
    #sets up the first agenda set
    for eachConnected in ways[node1]:
        nodeID = eachConnected[0]

        agenda.add(((node1, nodeID), great_circle_distance(nodesCords[node1], nodesCords[nodeID]), great_circle_distance(nodesCords[nodeID], nodesCords[node2])))
    
    while agenda != set():
        #sets our starter lowest to any arbitrary agenda element
        for elem in agenda:
            lowest = elem
            break
        
        #finds the actual element with the lowest estimated distance
        for elem in agenda: 
            if (lowest[1] + lowest[2]) > (elem[1]+elem[2]):
                lowest = elem
                
        path = lowest[0]
        calculatedDistance = lowest[1]
        terminalNode = path[len(path)-1]
        agenda.remove(lowest)
        
        if terminalNode not in expanded: 
            #checks if this is our final destination
            if terminalNode == node2:
                return path
            
            expanded.add(terminalNode)
            
            for eachTuple in ways[terminalNode]:
                child = eachTuple[0]
                if child not in expanded:
                    agenda = add_to_agenda(nodesCords, agenda, (path+(child,), calculatedDistance), node2)
        
    return None
        
        
def add_to_agenda_weighted(nodes, agenda, pathToAdd, destination, speed):
    '''
    Parameters
    ----------
    agenda : (set) is a set full of tuples, each tuple with 3 elements: the first element
    is a list with a path to be considered, second is the calculated length of that path and the third is 
    the predicted length from the end of that path to the destination
    pathToAdd : a tuple: the first element being the path that needs to be added and the second is the 
    calculated length of that path before the last node on that path was added
    destination : the final node ID they that we are trying to reach

    Returns
    -------
    The new agenda version

    '''
    #calculates the distance from the previous node to that node
    path = pathToAdd[0]
    lastStretch = great_circle_distance(nodes[path[len(path)-1]], nodes[path[len(path)-2]])
    #estimates the distance from that node to the final destination
    calculatedDistance = pathToAdd[1] + lastStretch/speed
    estimated = great_circle_distance(nodes[path[len(path)-1]], nodes[destination])/100

    agenda.add((path, calculatedDistance, estimated))
    
    return agenda       


def find_short_path(aux_structures, loc1, loc2):
    """
    Return the shortest path between the two locations

    Parameters:
        aux_structures: the result of calling build_auxiliary_structures
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of distance) from loc1 to loc2.
    """
    
    nodeCords = aux_structures[0]
    
    closest1 = (0,0)
    closest2 = (0, 0)
    ID1=0
    distanceOldTo1 = great_circle_distance( closest1, loc1) 
    distanceOldTo2 = great_circle_distance( closest2, loc2) 
    #finds the nodes with the cordinates closest to the given latitues and longitudes
    for eachCord in nodeCords:
        
        #(, -71.107667)
        distanceNewTo1 = great_circle_distance( nodeCords[eachCord], loc1) 
        distanceNewTo2 = great_circle_distance( nodeCords[eachCord], loc2) 

        
        if distanceNewTo1 < distanceOldTo1:
            closest1 = nodeCords[eachCord]
            ID1 = eachCord
            distanceOldTo1 = distanceNewTo1
            
            
        if distanceNewTo2 < distanceOldTo2: 
            closest2 = nodeCords[eachCord]
            ID2 = eachCord
            distanceOldTo2 = distanceNewTo2
    
    
    #with the 2 nodes found, just calls the function to find the closes path between them        
    path = find_short_path_nodes(aux_structures, ID1, ID2)

    if path == None:
        return None
    newPath = []
    #transforms the path of node IDs to one of latitudes and longitudes
    for elem in path:
        newPath.append(nodeCords[elem])
    
    return newPath

def find_short_path_nodes_weighted(aux_structures, node1, node2):
    """
    Return the shortest path between the two nodes

    Parameters:
        aux_structures: the result of calling build_auxiliary_structures
        node1: node representing the start location
        node2: node representing the end location

    Returns:
        a list of node IDs representing the shortest path (in terms of
        distance) from node1 to node2
    """
    nodesCords = aux_structures[0]
    ways = aux_structures[1]
    agenda = set()
    expanded = set()
    #sets up first agenda set
    for eachConnected in ways[node1]:
        nodeID = eachConnected[0]
        if eachConnected[2] == 0:
            speed = DEFAULT_SPEED_LIMIT_MPH[eachConnected[1]]
        else:
            speed = eachConnected[2]
 
        agenda.add(((node1, nodeID), great_circle_distance(nodesCords[node1], nodesCords[nodeID])/speed, great_circle_distance(nodesCords[nodeID], nodesCords[node2])/100))
    
    while agenda != set():
         #sets our starter lowest to any arbitrary agenda element
        for elem in agenda:
            lowest = elem
            break
        
        for elem in agenda: 
            if (lowest[1] + lowest[2]) > (elem[1]+elem[2]):
                lowest = elem
                
        path = lowest[0]
        calculatedDistance = lowest[1]
        terminalNode = path[len(path)-1]
        agenda.remove(lowest)
        
        #checks if this is our final destination
        if terminalNode not in expanded: 
            if terminalNode == node2:
                return path
            
            expanded.add(terminalNode)
            #adds all the nodes it connects to the agenda
            for eachTuple in ways[terminalNode]:
                child = eachTuple[0]
                if eachTuple[2] == 0:
                    speed = DEFAULT_SPEED_LIMIT_MPH[eachTuple[1]]
                else:
                    speed = eachTuple[2]
                if child not in expanded:
                    agenda = add_to_agenda_weighted(nodesCords, agenda, (path+(child,), calculatedDistance), node2, speed)
        
    return None


def find_fast_path(aux_structures, loc1, loc2):
    """
    Return the shortest path between the two locations, in terms of expected
    time (taking into account speed limits).

    Parameters:
        aux_structures: the result of calling build_auxiliary_structures
        loc1: tuple of 2 floats: (latitude, longitude), representing the start
              location
        loc2: tuple of 2 floats: (latitude, longitude), representing the end
              location

    Returns:
        a list of (latitude, longitude) tuples representing the shortest path
        (in terms of time) from loc1 to loc2.
    """
    nodeCords = aux_structures[0]
    
    closest1 = (0,0)
    closest2 = (0, 0)
    ID1=0
    distanceOldTo1 = great_circle_distance( closest1, loc1) 
    distanceOldTo2 = great_circle_distance( closest2, loc2) 
    #transforms the given coordinates into the closest given nodes to them
    for eachCord in nodeCords:
        
        #(, -71.107667)
        distanceNewTo1 = great_circle_distance( nodeCords[eachCord], loc1) 
        distanceNewTo2 = great_circle_distance( nodeCords[eachCord], loc2) 

        
        if distanceNewTo1 < distanceOldTo1:
            closest1 = nodeCords[eachCord]
            ID1 = eachCord
            distanceOldTo1 = distanceNewTo1
            
            
        if distanceNewTo2 < distanceOldTo2: 
            closest2 = nodeCords[eachCord]
            ID2 = eachCord
            distanceOldTo2 = distanceNewTo2
            
    path = find_short_path_nodes_weighted(aux_structures, ID1, ID2)

    if path == None:
        return None
    newPath = []
    #transforms the path of nodes into a path of coordinates
    for elem in path:
        newPath.append(nodeCords[elem])
    
    return newPath


if __name__ == '__main__':
    # additional code here will be run only when lab.py is invoked directly
    # (not when imported from test.py), so this is a good place to put code
    # used, for example, to generate the results for the online questions.
    '''
    print(find_fast_path(build_auxiliary_structures('resources/mit.nodes', 'resources/mit.ways'), (42.355, -71.1009), (42.3612, -71.092)))
    
    i = 0
    finding = (42.355, -71.1009)
    for node in read_osm_data('resources/mit.nodes'):
        if node['lat']== finding[0] and node['lon'] == finding[1]:
            print(node['id'])
    '''
    #print(build_auxiliary_structures('resources/mit.nodes', 'resources/mit.ways'))
    #print(find_short_path_nodes(build_auxiliary_structures('resources/mit.nodes', 'resources/mit.ways'), 6, 7))
    
    
    
    '''
    print(find_short_path(build_auxiliary_structures('resources/midwest.nodes', 'resources/midwest.ways'), (42.359242, -71.093765), (42.360485, -71.108349)))
    print('weird')
    for node in read_osm_data('test_data/test_cambridge_01_short.pickle'):
        print(node)
    '''
    '''
    passedBy = False
    for node in read_osm_data('resources/midwest.ways'):
        if node['id'] == 21705939:
            print(node)
            
            connecting = node['nodes']
            nodesLocs = {}
            totalPathDistance = 0
            
            
    for node in read_osm_data('resources/midwest.nodes'):
        if node['id'] in connecting:
            nodesLocs[node['id']] = (node['lat'], node['lon'])
    
    for i in range(len(connecting) - 1):
        totalPathDistance += great_circle_distance(nodesLocs[connecting[i]], nodesLocs[connecting[i+1]])
        
    print(totalPathDistance)
    '''
    '''
    for node in read_osm_data('resources/midwest.nodes'):
        
        if node['id'] == 233941454:
            loc1 = (node['lat'], node['lon'])
            if passedBy == True:
                break
            passedBy = True
            
        if node['id'] == 233947199:

            loc2 = (node['lat'], node['lon'])
            if passedBy == True:
                break
            passedBy = True
            
    print(great_circle_distance(loc1, loc2))
    '''
            
    '''
        if 'name' in node['tags']:
            if node['tags']['name'] == '77 Massachusetts Ave':
                print(node['id'])
    print(i)
    
    print(great_circle_distance((42.363745, -71.100999), (42.361283, -71.239677)))

    i=0
    s=0
    for node in read_osm_data('resources/cambridge.ways'):
        if 'oneway' in node['tags']:
            if node['tags']['oneway'] == 'yes':
                i+=1
        

    print(i)
    '''