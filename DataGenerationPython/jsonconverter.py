# Copyright 2014 Dr. Greg M. Bernstein
""" Helper functions for reading and writing JSON representations of various network path,
    demand, and other entities.

    See the IPython note book: JSON_Conversion.ipynb for more in depth explanation of the
    whys and hows to use these methods.  Or just look at the example code at the end of
    the file.
"""
import json


def demands_to_j(obj):
    """ A function to partially convert a demand dictionary to JSON format.

        Parameters
        ----------
        obj : dictionary
            a demand dictionary, indexed by a node pair, with value the demand volume.

        Returns
        -------
        list_of_dicts : list
            a list of dictionaries that can readily be converted to JSON with the json
            standard library routines.
    """
    tmp = []
    for d in obj.keys():
        tmp.append({"source": d[0], "target": d[1], "demand": obj[d]})
    return tmp

def j_to_demands(d_list):
    """ Helps read in a demand dictionary from a JSON object.

        Parameters
        ----------
        d_list : list
            a list of Python dictionaries representing the JSON demand and has
            source, target, and demand keys.

        Returns
        -------
        demands : dictionary
            a demand dictionary, indexed by a node pair, with value the demand volume.
    """
    tmp = {}
    for d in d_list:
        tmp[d["source"], d["target"]] = d["demand"]
    return tmp

def paths_to_j(path_dict):
    """ Takes a candidate paths dictionary and converts it to a JSON serializable form.

        Parameters
        ----------
        path_dict : dictionary
            a dictionary indexed by a node pair whose value is a list of paths, where each path
            is a list of nodes.

        Returns
        -------
        list_dict : list
            a list of dictionaries that can readily be converted to JSON with the json
            standard library routines.
    """
    tmp = []  # We'll use a list
    for k in path_dict.keys():
        tmp.append({"source": k[0], "target": k[1], "paths": path_dict[k]})
    return tmp

def j_to_paths(path_list):
    """ A helper function to retrieve a candidate paths dictionary from JSON.

        Parameters
        ----------
        path_list : list
            a list of dictionaries, each representing a JSON path candidate
            object with from, to, and paths keywords.

        Returns
        -------
        path_dict : dictionary
            a dictionary indexed by a node pair whose value is a list of paths, where each path
            is a list of nodes.
    """
    tmp = {}
    for p in path_list:
        tmp[p["source"],p["target"]] = p["paths"]
    return tmp


if __name__ == "__main__":
    paths = {(1, 2): [[1, 2], [1, 3, 2]],
     (1, 3): [[1, 3], [1, 2, 3]],
     (2, 1): [[2, 1]],
     (2, 3): [[2, 3]],
     (3, 1): [[3, 1], [3, 2, 1]],
     (3, 2): [[3, 2]]}

    demands = {(1, 2): 5, (1, 3): 7, (2, 1): 5, (2, 3): 8, (3, 1): 7, (3, 2): 8}

    print json.dumps(demands_to_j(demands))
    print json.dumps(demands_to_j(demands), sort_keys=True)
    print "Now with indentation"
    print json.dumps(demands_to_j(demands), sort_keys=True, indent=4)
    demand_string = '[{"source": 1, "target": 2, "demand": 5}, {"source": 3, "target": 2, "demand": 8}, {"source": 1, "target": 3, "demand": 7}, \
        {"source": 3, "target": 1, "demand": 7}, {"source": 2, "target": 1, "demand": 5}, {"source": 2, "target": 3, "demand": 8}]'
    # Try deserializing the above JSON string
    demands2 = j_to_demands(json.loads(demand_string))
    print demands2
    print demands2 == demands

    print json.dumps(paths_to_j(paths))
    # Example JSON string for candidate paths
    path_string = '[{"target": 2, "source": 1, "paths": [[1, 2], [1, 3, 2]]}, \
    {"target": 2, "source": 3, "paths": [[3, 2]]}, {"target": 3, "source": 1, "paths": [[1, 3], [1, 2, 3]]},\
    {"target": 1, "source": 3, "paths": [[3, 1], [3, 2, 1]]}, {"target": 1, "source": 2, "paths": [[2, 1]]},\
    {"target": 3, "source": 2, "paths": [[2, 3]]}]'
    # Try converting from JSON path string back to a candidate path dictionary
    paths2 = j_to_paths(json.loads(path_string))
    print paths == paths2
    print paths2