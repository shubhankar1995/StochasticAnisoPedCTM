"""
module: YenKShortestPaths
-------------------------

Classes for computing the loopless k-shortest path problem via
Yen's method. This implementation uses a modified Dijkstra algorithm
for computing shortest paths to allow its use in diverse route computations.

Author: *Greg Bernstein*
Modified: Shubhankar Mathur
"""

import networkx as nx
import heapq
from ModifiedDijkstra import ModifiedDijkstra
from copy import deepcopy


class YenKShortestPaths(object):
    """
     This is a straight forward implementation of Yen's K shortest loopless path algorithm. No attempt 
     has been made to perform any optimization that have been suggested in the literature. Our main goal 
     was to have a functioning K-shortest path  algorithm. This implementation should work for both 
     undirected and directed  graphs. However it has only been tested so far against undirected graphs.
    """

    def __init__(self, graph, source, dest, weight="weight", cap="capacity"):
        """
        Constructor

                @param source    The beginning node of the path.
                @param dest      The termination node of the path.
        """
        self.wt = weight
        self.cap = cap
        self.g = graph
        self.pathHeap = []  # Use the heapq module functions heappush(pathHeap, item) and heappop(pathHeap, item)
        self.pathList = []  # Contains WeightedPath objects
        self.deletedEdges = set()
        self.deletedNodes = set()
        self.kPath = None
        # Make a copy of the graph tempG that we can manipulate
        if isinstance(graph, nx.Graph):
            self.tempG = graph.copy()
        else:
            self.tempG = None
        self.kPath = None
        self.pathHeap = []
        self.pathList = []
        self.source = source
        self.dest = dest

    def __iter__(self):
        """Returns itself as an iterator object"""
        return self

    def next(self):
        """
        Computes successive shortest path. Each one will have
        a length (cost) greater than or equal the previously generated algorithm.
        Returns null if no more paths can be found.
        You must first call findFirstShortestPath(source, dest) to initialize the
        algorithm and set the source and destination node.
        @return  the next shortest path (or the next longer path depending on
        how you want to think about things).
        """
        if self.kPath is None:
            alg = ModifiedDijkstra(self.g, self.wt)
            nodeList = alg.getPath(self.source, self.dest, as_nodes=True)
            if len(nodeList) == 0:
                raise StopIteration
            deletedLinks = set()
            self.kPath = WeightedPath(nodeList, deletedLinks, self.g, wt=self.wt, cap=self.cap)
            self.kPath.dNode = self.source
            self.pathList.append(self.kPath)
            return self.kPath
        # Iterate over all the nodes in kPath from dNode to the node before the destination
        # and add candidate paths to the path heap.
        kNodes = self.kPath.nodeList
        index = kNodes.index(self.kPath.dNode)
        curNode = kNodes[index]
        while curNode != self.dest:
            self._removeEdgesNodes(curNode)
            candidate = self._computeCandidatePath(curNode)
            self._restoreGraph()
            if candidate is not None:
                heapq.heappush(self.pathHeap, candidate)
            index += 1
            curNode = kNodes[index]
            
        if len(self.pathHeap) == 0:
            raise StopIteration

        p = heapq.heappop(self.pathHeap)  # after iterations contains next shortest path
        self.pathList.append(p)
        self.kPath = p  # updates the kth path
        return p

    def __lt__(self, other):
        return self.cost < other.cost

    def __eq__(self, other):
        return self.cost < other.cost

    def _removeEdgesNodes(self, curNode):
        """
        Remove all nodes from source to the node before the current node in kPath.
        Delete the edge between curNode and the next node in kPath
        Delete any edges previously deleted in kPath starting at curNode
        add all deleted edges to the deleted edge list.
        """
        # Figure out all edges to be removed first then take them out of the temp graph
        # then remove all the nodes from the temp graph.
        # At the start the temp graph is equal to the initial graph.
        self.deletedEdges = set()
        self.deletedNodes = set()
        kNodes = self.kPath.nodeList
        index = 0
        tempNode = kNodes[index]
        index += 1
        while tempNode != curNode:
            edges = self.tempG.edges(tempNode)
            if len(edges) != 0:
                for edge in deepcopy(edges):
                    self.deletedEdges.add(edge)
                    self.tempG.remove_edge(edge[0], edge[1])

            self.deletedNodes.add(tempNode)
            self.tempG.remove_node(tempNode)
            tempNode = kNodes[index]
            index += 1
        # Also need to remove those old deleted edges that start on curNode
        oldDelEdges = self.kPath.deletedEdges
        if self.g.is_directed():
            outEdges = self.g.out_edges(curNode)
        else:
            outEdges = self.g.edges(curNode)

        for  e in outEdges:
            if e in oldDelEdges:
                self.deletedEdges.add(e)
                self.tempG.remove_edge(e[0], e[1])
        
        # Now delete the edge from the curNode to the next in the path
        tempNode = kNodes[index]
        e = (curNode, tempNode)
        self.deletedEdges.add(e)
        self.tempG.remove_edge(curNode, tempNode)

    def _computeCandidatePath(self, curNode):
        """
        Compute the shortest path on the modified graph and then
        combines with the portion of kPath from the source up through
        the deviation node
        """
        alg = ModifiedDijkstra(self.tempG, self.wt)
        nodeList = alg.getPath(curNode, self.dest, as_nodes=True)
        # Trying this out...
        if nodeList is None:
            return None

        # Get first part of the path from kPath
        nodePath = []
        if curNode in self.kPath.nodeList:
            index = self.kPath.nodeList.index(curNode)
            nodePath = self.kPath.nodeList[0:index]

        nodePath.extend(nodeList)
        wp = WeightedPath(nodePath, self.deletedEdges, self.g, wt=self.wt, cap=self.cap)
        wp.dNode = curNode
        return wp
    
    def _restoreGraph(self):
        """
        Using the internal deleted node and deleted edge containers
        restores the temp graph to match the graph g.
        """
        self.tempG = self.g.copy()
        self.deletedEdges = []
        self.deletedNodes = []
    
    
class WeightedPath(object):
    """Used internally by the Yen k-shortest path algorithm.
    Also return to user as a result.
    """
    def __init__(self, pathNodeList, deletedEdges, g, wt='weight', cap='capacity'):
        """
        Constructor
        """
        self.nodeList = pathNodeList
        self.deletedEdges = set(deletedEdges)
        self.g = g
        self.wt = wt
        self.dNode = None   # The deflection node
        self.cost = 0.0
        self.capacity = float("inf")
        for i in range(len(pathNodeList)-1):
            self.cost = self.cost + g[pathNodeList[i]][pathNodeList[i+1]][0][wt]
            if cap is not None:
                self.capacity = self.capacity                  # min(self.capacity, g[pathNodeList[i]][pathNodeList[i+1]][cap])
            else:
                self.capacity = None
    
    def __lt__(self, other):
        return self.cost < other.cost

    def __eq__(self, other):
        return self.cost < other.cost
    '''
    def __cmp__(self, other):
        if other is None:
            return -1
        return cmp(self.cost, other.cost)
    '''
    def __str__(self):
        return "nodeList: {}, cost: {}, capacity: {}".format(self.nodeList, self.cost, self.capacity)
