"""
module: ModifiedDijkstra
-------------------------
A slightly generalized version of the Dijkstra algorithm.

Author: *Greg Bernstein*
Modified: Shubhankar Mathur
"""


class ModifiedDijkstra(object):
    """
    The Modified Dijkstra algorithm from "Survivable Networks" by Ramesh Bhandari.
    This algorithm works with graphs that can have directed or undirected links.
    In addition, this algorithm can correctly function in some cases of negative
    arc lengths that arise in the disjoint path computations.

    Works with graphs, *g*, in NetworkX format. Specifically Graph and
    DiGraph classes.
    """
    def __init__(self, g, wt="weight"):
        """
        Constructor. Parameter *g* is a NetworkX Graph or DiGraph instance.
        The *wt* keyword argument sets the link attribute to be used in computing
        the path length.
        """
        self.dist = {}  # A map from nodes to their labels (float)
        self.predecessor = {}  # A map from a node to a node
        self.g = g
        self.wt = wt
        edges = g.edges()
        # Set the value for infinite distance in the graph
        self.inf = 0.0
        for e in edges:
            self.inf += abs(g[e[0]][e[1]][0][wt])
        self.inf += 1.0

    def getPath(self, source, dest, as_nodes=False):
        """
        Computes the shortest path in the graph between the given *source* and *dest*
        node (strings).  Returns the path as a list of links (default) or as a list of
        nodes by setting the *as_nodes* keyword argument to *True*.
        """
        self.dist = {}  # A map from nodes to their labels (float)
        self.predecessor = {}  # A map from a node to a node

        # Initialize the distance labels to "infinity"
        vertices = self.g.nodes()
        for vertex in vertices:
            self.dist[vertex] = self.inf
            self.predecessor[vertex] = source

        # Further set up the distance from the source to itself and
        # to all one hops away.
        self.dist[source] = 0.0
        if self.g.is_directed():
            outEdges = self.g.out_edges([source])
        else:
            outEdges = self.g.edges([source])
        for edge in outEdges:
            self.dist[edge[1]] = self.g[edge[0]][edge[1]][0][self.wt]
        
        s = set(vertices)
        s.remove(source)
        currentMin = self._findMinNode(s)
        if currentMin is None:
            return None
        s.remove(currentMin)
        while currentMin != dest and (len(s) != 0) and currentMin is not None:
            if self.g.is_directed():
                outEdges = self.g.out_edges([currentMin])
            else:
                outEdges = self.g.edges([currentMin])
            for edge in outEdges:
                opposite = edge[1]
                if self.dist[currentMin] + self.g[edge[0]][edge[1]][0][self.wt] < self.dist[opposite]:
                    self.dist[opposite] = self.dist[currentMin] + self.g[edge[0]][edge[1]][0][self.wt]
                    self.predecessor[opposite] = currentMin
                    s.add(opposite)
                
            currentMin = self._findMinNode(s)
            if currentMin is None:
                return None
            s.remove(currentMin)
        
        # Compute the path as a list of edges
        currentNode = dest
        predNode = self.predecessor.get(dest)
        node_list = [dest]
        done = False
        path = []
        while not done:
            path.append((predNode, currentNode))
            currentNode = predNode
            predNode = self.predecessor[predNode]
            node_list.append(currentNode)
            done = currentNode == source
        node_list.reverse()
        if as_nodes:
            return node_list
        else:
            return path
    

    def _findMinNode(self, s):
        """
        Finds the vertex with the minimum distance label in the set "s".
        returns the minimum vertex
        """
        minNode = None
        minVal = self.inf
        for vertex in s:
            if self.dist[vertex] < minVal:
                minVal = self.dist[vertex]
                minNode = vertex
        return minNode
