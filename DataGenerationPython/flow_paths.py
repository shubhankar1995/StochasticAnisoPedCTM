# Copyright 2014 Dr. Greg M. Bernstein
""" A function and its helpers to convert a flow into simple conformal paths.
    In particular these functions are very useful when interpreting the solutions
    of network design problems that utilize a **node-link** formulation.
"""

from sys import float_info
import copy


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


def getAllPathsInfo(demands, d_links, g, wt="weight"):
    """ Gets info on all the solution paths from the demand-link solution variables

    Parameters
    ----------

    demands : dictionary
        dictionary of original problem demands. Note that the demand volumes are not used just
        the demand pairs.
    d_links : dictionary
        dictionary of demand-link solution variables. These are the result of solving a design problem
        in node-link form.
    g : networkx.DiGraph
        The directed graph of the network.
    wt : string
        (optional) the link attribute to be used when computing path costs.

    Returns
    -------
    path_list : list
        A list of path dictionaries with node-list, cost, and capacity information.
    """
    print d_links
    all_paths = []
    for d in demands.keys():
        d_paths = flowToPaths(d, d_links[d])
        for i in range(len(d_paths[0])):
            tmp_path = {"capacity": d_paths[0][i], "nodeList": d_paths[1][i],
                        "cost": pathCost(d_paths[1][i], g, wt=wt)}
            all_paths.append(tmp_path)
    return all_paths


def flowToPaths(demand, gflow):
    """ Given a flow corresponding to a demand, realizes it via one or more paths.
        This is based on the outline of the proof of the
        conformal realization theorem which is given as an excercise in [1].

        [1] *D. P. Bertsekas*, **Network Optimization: Continuous
        and Discrete Models**. Athena Scientific, 1998.

        Parameters
        ----------
        demand : tuple
            a pair of nodes identifiers indicating the source and sink of the flow.
        gflow : list
            a list of nested tuples (edge, flow value) where edge = (nodeA, nodeB)

        Returns
        -------
        paths : list
            a tuple of a list of the paths loads and a list of the corresponding paths
    """
    loads = []
    #path_link_list = []
    path_node_list = []
    path_load, link_list, flow = _flowToPath(demand, gflow, append=True)
    #print "First link list: {}".format(link_list)
    loads.append(path_load)
    #path_link_list.append(link_list)
    path_node_list.append(_linkListToNodeList(demand, link_list))
    reduced_flow = _reduceFlowByLoad(path_load, link_list, flow)
    #print "First reduced flow: {}".format(reduced_flow)

    while len(reduced_flow) > 0:
        load, link_list, reduced_flow = _flowToPath(demand, reduced_flow, append=False)
        loads.append(load)
        #path_link_list.append(link_list)
        path_node_list.append(_linkListToNodeList(demand, link_list))
        reduced_flow = _reduceFlowByLoad(load, link_list, reduced_flow)

    return loads, path_node_list


def _reduceFlowByLoad(load, link_list, flow):
    """
    Reduces the flow by the load on the links in the list.
    Removes links from the flow with no more flow, i.e., zero flow.
    """
    flow2 = []
    for tmp in flow:
        if tmp[0] in link_list:
            # subtract load
            if abs(tmp[1] - load) > float_info.epsilon*10000.0*(tmp[1]+load):
                flow2.append((tmp[0], tmp[1] - load))
        else:
            flow2.append(tmp)
    return flow2


def _flowToPath(demand, gflow, append=True):
    """Here we find the smallest capacity path within a flow.
    Returns the load of the smallest path within the flow, the links
    that make up the path, and the flow.
    Based on the conformal realization theorem algorithm in
    [1] D. P. Bertsekas and D. P. Bertsekas, Network Optimization: Continuous
    and Discrete Models. Athena Scientific, 1998.
    """
    flow = copy.deepcopy(gflow)
    node_set = set()
    for link_load in flow:
        node_set.add(link_load[0][0])  # Adds the source node
        node_set.add(link_load[0][1])  # Adds the destination node

    # compute the divergence of each node
    div_dict = {}
    for node in node_set:
        div_dict[node] = 0
    for link_load in flow:
        div_dict[link_load[0][0]] += link_load[1]  # the flow leaving the node
        div_dict[link_load[0][1]] += -link_load[1]  # the flow entering the node
    # check equality of source and destination divergence
    #print "Div Dictionary: {}".format(div_dict)
    tmp = div_dict[demand[0]] + div_dict[demand[1]]
    zero_compare = 1000.0*float_info.epsilon*abs(div_dict[demand[0]])
    if append:
        if tmp > zero_compare:
            raise Exception("Source and Sink flows don't seem to correspond")
        for node in node_set:
            if node != demand[0] and node != demand[1]:
                if div_dict[node] > zero_compare:
                    #print "Flow during exception: {}".format(flow)
                    raise Exception("Demands and flows don't seem to correspond")

    # Append artificial link for source and destination demands per Bertsekas
    if append:
        special_node = "*S*"
        flow.append(((special_node, demand[0]), div_dict[demand[0]]))
        flow.append(((demand[1], special_node), div_dict[demand[0]]))
        node_set.add(special_node)
    # Pick a link with the minimum flow
    def flow_load(flow):
        return flow[1]
    sel_link = min(flow, key=flow_load)
    #print "Selected link: {}".format(sel_link)
    # Now we can get to work
    set_list = []
    node_labels = {}
    tmp = set()
    tmp.add(sel_link[0][1])  # Adds the target node of the link
    node_labels[sel_link[0][1]] = sel_link[0]
    set_list.append(tmp)
    k = 0  # Set index
    set_union = tmp

    while set_union < node_set:
        tmp = set()
        # Check over all nodes in the current set indexed by k
        for m in set_list[k]:
            # Check for a link from m to a node n not in the set_union
            # if so add it to the current set
            for f in flow:
                if (f[0][0] == m) and (f[0][1] not in set_union):
                    tmp.add(f[0][1])
                    node_labels[f[0][1]] = f[0]
        if len(tmp) == 0:
            break
        k += 1
        set_list.append(tmp)
        set_union = set_union | tmp
    #
    # Now Bertsekas says to "traceback from sel_link[0][0] to sel_link[0][1] through the
    # node labels.
    link_list = []
    link_list.append(sel_link[0])
    #print "Node labels: {}".format(node_labels)
    start = sel_link[0][0]
    end = sel_link[0][1]
    link_list.append(node_labels[start])
    while node_labels[start][0] != end:
        start = node_labels[start][0]
        link_list.append(node_labels[start])
    #print "Trace Back Link List: {}".format(link_list)

    return sel_link[1], link_list, flow

def _linkListToNodeList(demand,link_list):
    """
    Takes a list of links and recovers the path between the
    end points in the demand. Note that the link_list may have
    some "fictious" links to the artificial node that gets
    inserted in the conformal realization algorithm.
    """
    node_list = []
    cur_node = demand[0]

    keep_going = True
    while keep_going:
        node_list.append(cur_node)
        next_node = None
        for link in link_list:
            if link[0] == cur_node:
                next_node = link[1]
        #
        keep_going = cur_node != demand[1]
        if keep_going and next_node == None:
            raise Exception("Bad path list")
        else:
            cur_node = next_node

    return node_list


def getDemandLinks(demands, link_list, flow_vars, no_splitting=False):
    """ Searches the solution values of the flow variables for "non-zero" link demand values.

        Parameters
        ----------
        demands : dictionary
            a demand dictionary indexed by a demand pair and whose value is the volume
        link_list : list
            a list of links (edges) of the network as node tuples.
        flow_vars : dictionary
            a dictionary of link, demand variables. In our case we are working with
            the solutions that have been returned from the solver. These are of type
            PuLP LpVariables.

        Returns
        -------
        used_links : dictionary
            a dictionary indexed by a demand pair whose value is a nested tuple of (link, load) where
            link is a node pair (tuple).

            For example:
            {('N0', 'N2'): [((u'N0', u'N1'), 16.0), ((u'N1', u'N2'), 16.0)],
            ('N0', 'N3'): [((u'N0', u'N6'), 25.0), ((u'N6', u'N3'), 25.0)],
            ('N1', 'N6'): [((u'N0', u'N6'), 25.0), ((u'N1', u'N0'), 25.0)],
            ('N2', 'N3'): [((u'N2', u'N3'), 29.0)],
            ('N3', 'N5'): [((u'N3', u'N4'), 31.0), ((u'N4', u'N5'), 31.0)]}

    """
    demand_links = {}
    if no_splitting:
        zero_test = float_info.epsilon

    for d in demands.keys():
        flow_list = []
        for e in link_list:
            if not no_splitting:
                zero_test = float_info.epsilon*demands[d]
            if flow_vars[e,d].value() > zero_test:
                flow_list.append((e, flow_vars[e,d].value()))
        demand_links[d] = flow_list

    return demand_links