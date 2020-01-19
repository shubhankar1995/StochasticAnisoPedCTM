package anisopedctm;

import java.util.Enumeration;
import java.util.HashSet;
import java.util.Hashtable;
import java.util.Set;

/**
 * Potential Field class
 *
 * @author Flurin Haenseler, Gael Lederrey
 *
 * @version StochasticAnisoPedCTM v1.0
 * @author Shubhankar Mathur
 *
 */

public class PotentialField {
	//compute node potentials for all routes, and pre-compute route choice model
	public void computeAllNodePotentials(Hashtable<Integer, Link> linkList, Hashtable<Integer, Node> nodeList,
			Hashtable<String, Route> routeList, HashSet<Integer> sourceSinkNodes, Parameter param, Hashtable<String, Blockage> blockageList, int timeStep) {

		//compute route-specific node potentials for each route
		Enumeration<String> routeNames = routeList.keys();
		String curRouteName; //name of current route

		while(routeNames.hasMoreElements()) {
			curRouteName = routeNames.nextElement(); //retrieve current route name

			//compute node potentials for all nodes for given route
			computeNodePotentialsForRoute(curRouteName, linkList, nodeList, routeList, sourceSinkNodes, blockageList, timeStep);
		}

		//pre-compute route-specific denominators for route choice model
		for (Node curNode : nodeList.values()) {
			curNode.computeRouteChoiceDenominator(linkList, nodeList, param);
		}
	}


	//compute potential field associated with a route using Dijkstra's algorithm
	//node potential = minimum distance from destination in non-dimensional time
	//potential at destination node = 0
	public void computeNodePotentialsForRoute(String routeName, Hashtable<Integer, Link> linkList,
			Hashtable<Integer, Node> nodeList, Hashtable<String, Route> routeList, HashSet<Integer> sourceSinkNodes,
			Hashtable<String, Blockage> blockageList, int timeStep) {

		//current route
		Route curRoute = routeList.get(routeName);

		//set of nodes on current route
		final Set<Integer> routeNodeIDs = curRoute.getRouteNodes();

		//set of relevant, unvisited nodes on current route
		Set<Integer> unvisitedNodeIDs = new HashSet<Integer>(routeNodeIDs);

		for (int curNodeID : routeNodeIDs) {
			//initialize all nodes with infinite potential
			Node node = nodeList.get(curNodeID); 
			node.setPotential(routeName, Double.MAX_VALUE);
		}

		//initialize destination node
		int destNodeID = curRoute.getDestNodeID();
		nodeList.get(destNodeID).setPotential(routeName, 0.0);
		
		//blockagePercent of node
		Double blockagePercent = 0.0;
		while ( !unvisitedNodeIDs.isEmpty() ){

			//next node: unvisited node with lowest potential (destination in first iteration)
			int nextNodeID = Integer.MAX_VALUE;
			double nextNodePot = Double.MAX_VALUE;

			double candNodePot; //potential of candidate node
			Node candNode;
			//determine next node by iterating over set of unvisited nodes
			//next node is node with lowest potential (destination node in first case)
			for (int candNodeID : unvisitedNodeIDs) {
				candNode = nodeList.get(candNodeID);
				candNodePot = candNode.getPotential(routeName);
				blockagePercent = getNodeBlockagePercent(candNode, linkList, blockageList, timeStep);
                                
                                if (blockagePercent == 0.0 ){
                                    blockagePercent = 1.0;
                                }
                                
				candNodePot = candNodePot;// * (100 + blockagePercent)/100;
				
				//System.out.println("candNodeID: " + candNodeID);
				//System.out.println("candNodePot: " + candNodePot);

				//if candidate node has lower potential, consider it as next node
				if (candNodePot <= nextNodePot){
					nextNodeID = candNodeID;
					nextNodePot = candNodePot;
				}
			}


			//System.out.println("nextNodeID: " + nextNodeID);
			//System.out.println("nextNodePot: " + nextNodePot);

			//check if a valid next node has been found
			if (nextNodeID == Integer.MAX_VALUE) {
				throw new RuntimeException("Invalid next node");
			}

			//remove next node from set of unvisited nodes
			unvisitedNodeIDs.remove(nextNodeID);

			int neighborNodeID; //node of neighbor of next node
			double linkTravelTime; //relative travel time on link connecting next node and neighbor
			double neighborCurPot; //current potential of neighbor
			double neighborCandPot; //alternative new potential of neighbor
			Node neighbourNode;
			
			//iterate through neighbors of nextNode
			for (int outLinkID : nodeList.get(nextNodeID).getOutLinks()) {
				//destination node of outLink
				neighborNodeID = linkList.get(outLinkID).getDestNode();
				
				
				//check if neighbor is in set of feasible, unvisited nodes
				if (unvisitedNodeIDs.contains(neighborNodeID)) {
					//get current potential of neighbor
					neighborCurPot = nodeList.get(neighborNodeID).getPotential(routeName);
					
					neighbourNode = nodeList.get(neighborNodeID);
					blockagePercent = getNodeBlockagePercent(neighbourNode, linkList, blockageList, timeStep);
					
					//get link travel time and compute candidate potential
					linkTravelTime = linkList.get(outLinkID).getRelTravTime();
					neighborCandPot = nextNodePot + linkTravelTime;
                                        
                                        if (blockagePercent == 0.0 ){
                                            blockagePercent = 1.0;
                                        }
                                        
					neighborCandPot = neighborCandPot;// * blockagePercent; //(100 + blockagePercent)/100 ;
					
					//if alternative potential is lower than current potential, update
					if (neighborCandPot < neighborCurPot) {
                                            
						nodeList.get(neighborNodeID).setPotential(routeName, neighborCandPot);
					}
				}
			}

			// Now we will set the potential for all the Source/Sink nodes to infinity except if it's the destination
			// node of the current route.
			for(int i : sourceSinkNodes)
			{
				if(i != routeList.get(routeName).getDestNodeID())
				{
					nodeList.get(i).setPotential(routeName, Math.pow(10, 10));
				}
			}
		}
	}
	
	public Double getNodeBlockagePercent (Node node, Hashtable<Integer, Link> linkList, Hashtable<String, Blockage> blockageList, int timeStep) {
		Double blockagePercent = 0.0;
		
		int outLinkId = node.getOutLinks().stream().findFirst().get();
		String cellName = linkList.get(outLinkId).cellName;
		
		if(null != blockageList.get(cellName)) {
			Blockage blockage = blockageList.get(cellName);
			if(blockage.getStartTime() >= timeStep && timeStep <= blockage.getEndTime()) {
				blockagePercent = blockage.getBlockagePercent();
			}
		}
		
		return blockagePercent;
	}
}
