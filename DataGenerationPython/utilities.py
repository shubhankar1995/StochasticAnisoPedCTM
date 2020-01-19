# Copyright 2014 Dr. Greg M. Bernstein
""" A collection of methods to help in the formulation of network design problems,
    to aid in the generation of design problems, to generate candidates paths, and
    to aid in the analysis of raw solutions to design problems.
"""
from math import sqrt
from YenKShortestPaths import YenKShortestPaths
import random
import networkx as nx


def link_in_path(link, node_list):
    """ This function checks if the given link is in the path defined by this node list.
        Works with undirected graphs so checks both link orientations.

        Parameters
        ----------
        link : tuple
            a link expressed in a node pair tuple
        node_list : list
            a path as a list of nodes

        Returns
        -------
        indicator : boolean
            true is the link is in the path, false if not.
    """
    b_link = (link[1], link[0])  # The link in reverse order
    for i in range(len(node_list) - 1):
        p_link = (node_list[i], node_list[i+1])
        if link == p_link:
            return True
        if b_link == p_link:
            return True
    return False


def path_valid(g, p):
    """ Checks whether the list nodes p is a valid path in g.

        Parameters
        ----------
        g : networkx.Graph
            a directed or undirected graph
        p : list
            the path as a list of nodes

        Returns
        -------
        indicator : boolean
        True if the path is valid, False otherwise.
    """
    plen = len(p)
    for i in range(plen-1):
     if not g.has_edge(p[i],p[i+1]):
         return False
    return True


def pathCost(path, g, wt="weight"):
    """ Compute the cost of the given path in a graph.

    Parameters
    ----------
    path : list
        a path given as a node list.
    g : networkx.Graph
        a networkx graph or directed graph where links have some type of weight attribute.
    wt : string
        (optional) the name of the link attribute to be used to compute the (additive) path cost.

    Returns
    -------
    cost : float
        The total cost of the path.
    """
    cost = 0.0
    for i in range(len(path)-1):
        if not g.has_edge(path[i], path[i+1]):
            raise Exception('Bad Path')
        else:
            cost += g[path[i]][path[i+1]][wt]
    return cost


def pathCap(path, g, cap="capacity"):
    """ Compute the capacity of the given path in a graph.

    Parameters
    ----------
    path : list
        a path given as a node list.
    g : networkx.Graph
        a networkx graph or directed graph where links have some type of weight attribute.
    cap : string
        (optional) the name of the link attribute to be used to compute the capacity.

    Returns
    -------
    cap : float
        The capacity of the path.
    """
    p_cap = float("inf")
    for i in range(len(path)-1):
        if not g.has_edge(path[i], path[i+1]):
            raise Exception('Bad Path')
        else:
            p_cap = min(p_cap, g[path[i]][path[i+1]][cap])
    return p_cap


def wt_by_distance(g, wt='weight'):
    """ Sets the weights of links in a graph based on the distance between the end nodes.
        Modifies the graph g.

        Parameters
        ----------
        g : networkx.Graph
            A directed or undirected graph representing the network. Assumes nodes have
            x and y coordinate attributes.
    """
    for e in g.edges():
        xA = g.node[e[0]]['x']
        xZ = g.node[e[1]]['x']
        yA = g.node[e[0]]['y']
        yZ = g.node[e[1]]['y']
        distance = sqrt((xA - xZ)**2 + (yA - yZ)**2)
        g[e[0]][e[1]][wt] = distance
        
def randomize_cap(graph, cap_min, cap_max, cap="capacity"):
    ''' Randomizes the capacity of a links of a network within
    the ranges [cap_min, cap_max].
    '''
    for link in graph.edges():
        graph.edge[link[0]][link[1]][cap] = random.randrange(cap_min, cap_max)


def gen_cand_paths(g, demands, num):
    """ Generates demand path candidates.

        Parameters
        ----------
        g : networkx.Graph
            Graph representing the network.
        demands : dictionary
            A dictionary indexed by node pairs representing demands.
        num : integer
            The number of paths to be generated via a k-shortest path algorithm. Note that
            `num` simple paths may not exist and that the algorithm will return the maximum
            number of simple paths available.

        Returns
        -------
        paths : dictionary
            A dictionary indexed by demand (node) pairs, whose value is a list of paths with
            each path represented by a node list.
    """
    paths = {}
    k = num
    for d in demands.keys():
        paths[d] = []  # Start with an empty list of paths
        alg = YenKShortestPaths(g)
        p = alg.findFirstShortestPath(d[0], d[1])
        if p == None:
            break
        paths[d].append(p.nodeList)
        for i in range(k-1):
            p = alg.getNextShortestPath()
            if p == None:
                break
            paths[d].append(p.nodeList)
    return paths


def gen_rand_demands(node_list, n_pair, low, high):
    """ Used to generate pairs of demands between nodes in graph g.

        Parameters
        ----------
        node_list : list
            List of nodes that can generate demands
        n_pair : integer
            The number of demand pairs to generate
        low : float
        high : float
            The demand volume will be a floating point number in the range `low` to `high`.

        Returns
        -------
        demands : dictionary
            A dictionary whose keys are the demand (node) pairs and whose values
            are the demand volumes.
    """
    n = len(node_list)
    max_pair = n*(n - 1)/2  # max pairs that can be produced
    #print max_pair
    demands = {}
    while len(demands) < min(n_pair, max_pair):
        nodeA = random.choice(node_list)
        nodeB = random.choice(node_list)
        while nodeB == nodeA:
            nodeB = random.choice(node_list)
        if not demands.has_key((nodeA, nodeB)):
            if not demands.has_key((nodeB, nodeA)):
                demands[(nodeA, nodeB)] = random.uniform(low, high)
    return demands
    
def gen_rand_demands_dir(node_list, n_pair, low, high):
    """ Used to generate pairs of directed demands between nodes in graph g.

        Parameters
        ----------
        node_list : list
            List of nodes that can generate demands
        n_pair : integer
            The number of demand pairs to generate
        low : float
        high : float
            The demand volume will be a floating point number in the range `low` to `high`.

        Returns
        -------
        demands : dictionary
            A dictionary whose keys are the demand (node) pairs and whose values
            are the demand volumes.
    """
    n = len(node_list)
    max_pair = n*(n - 1)  # max pairs that can be produced
    #print max_pair
    demands = {}
    while len(demands) < min(n_pair, max_pair):
        nodeA = random.choice(node_list)
        nodeB = random.choice(node_list)
        while nodeB == nodeA:
            nodeB = random.choice(node_list)
        if not demands.has_key((nodeA, nodeB)):
            demands[(nodeA, nodeB)] = random.uniform(low, high)
    return demands

# [ "nodeList", "cost", "capacity"],
# ["nodeList" "cost", "ratio", "load"],
# ["time", "nodeList", "cost", "load"],
# ["nodeList"]

def paths_j(cand_paths, g):
    """ Gives nice information about candidate paths in JSON format.
        An example of the generated JSON could be:
        ["nodeList": ["N2", "N1", "N0"], "cost": 25, "capacity": 0.4375}, ...]

        Parameters
        ----------
        cand_paths : dictionary
            the dictionary of candidate paths
        g : networkx.Graph
            a graph compatible with the candidate paths

        Returns
        -------
        list_dicts : list
            a list of dictionaries, each representing a single path, ready to be
            converted to JSON with the Python json library module.
    """
    info_paths = []
    for d in cand_paths.keys():
        for p in cand_paths[d]:
            info = {"nodeList": p, "cost": pathCost(p, g), "capacity": pathCap(p, g)}
            info_paths.append(info)
    return info_paths

def sol_paths_j(g, d_paths, can_paths, demands):
    """ Gives nice information about solution paths in JSON format.
        Useful for processing results from **link-path** formulations.
        Example format: [{"load": 17.5, "nodeList": ["N2", "N1", "N0"], "cost": 25, "ratio": 0.4375}, ...]

        Parameters
        ----------
        g : networkx.Graph
            the graph
        d_paths : dictionary
            the solution demand paths; indexed by ((nA,nZ), p) where nA, nZ are the A and Z nodes of the demand,
            and p is the path index (integer).
        can_paths : dictionary
            the dictionary of candidate paths used in the problem (must correspond to d_path variables)
        demands : dictionary
            the demand dictionary used in the problem

        Returns
        -------
        path_list : list
            a list of dictionaries ready to be turned into JSON with the Python json library module.
    """
    info_paths = []
    for p in d_paths.keys():
        load = d_paths[p].varValue
        if load > 0.001 * demands[p[0]]:
            info = {"nodeList": can_paths[p[0]][p[1]], "load": load, "cost": pathCost(can_paths[p[0]][p[1]],g),
                    "ratio": load/demands[p[0]]}
            info_paths.append(info)
    return info_paths

def print_link_costs(g, wt='weight'):
    """ Prints a nicely format list of edges and their weights.
        Useful for import into MS Word or other documents. Uses ":" to separate columns since
        "," is already used in link node pairs.

        Parameters
        ----------
        g : networkx.Graph
            A graph with links with a `wt` attribute.
        wt : string
            Used to indicate the link attribute of interest.
    """
    for e in sorted(g.edges()):
        print "({},{}): {}". format(e[0],e[1], "%5.2f" % g[e[0]][e[1]][wt])


def sol_net(g, link_cap, link_mod, cap="capacity"):
    """ Creates the solution network, i.e., the network with only the properly dimensioned
        links included. Works with solutions to multi-modular dimensioning problems.

        Parameters
        ----------
        g : networkx.Graph
            the graph of the network describing the problem
        link_cap : dictionary
            a dictionary of solution variables for the modular link capacities
        link_mod : list
            a list of tuples of (module capacity, module cost)

        Returns
        -------
        g_sol : networkx.Graph
            the graph with only the dimensioned links installed.
    """
    g_sol = g.copy()
    for e in g.edges():
        e_cap = 0.0
        for i, m in enumerate(link_mod):
            e_cap += link_cap[e,i].varValue * m[0]  #
        g_sol[e[0]][e[1]][cap] = e_cap
    r_list = []
    cap = nx.get_edge_attributes(g_sol, cap)
    for e in g_sol.edges():
        if cap[e] < 0.5 * link_mod[0][0]:  # check for zero capacity link
            r_list.append(e)
    g_sol.remove_edges_from(r_list)
    return g_sol

def link_util(g, d_paths, can_paths):
    """ Computes the utilization of all links in the network.
        Works with solutions from *link-path* formulations.

        Parameters
        ----------
        g : networkx.Graph
            the network graph g
        d_paths : dictionary
            solution d_paths variables,
        can_paths : dictionary
            the candidate paths can_paths.
        Returns
        link_loads : dictionary
            a dictionary index by links with the load or utilization on each link.
    """
    util = {}
    for e in g.edges():
        util[e] = 0.0
        for d in can_paths.keys():
            for p in range(len(can_paths[d])):
                if link_in_path(e, can_paths[d][p]):
                    util[e] += d_paths[d, p].varValue
    return util
