package anisopedctm;

import java.util.HashSet;
import java.util.Set;

/**
 * Route class
 *
 * @author Flurin Haenseler, Gael Lederrey
 *
 * @version StochasticAnisoPedCTM v1.0
 * @author Shubhankar Mathur
 *
 */
public class Route {

    public final String[] zoneSeq; //zone sequence

    //origin and destination zones
    public final String origZone;
    public final String destZone;

    //linkID of source and sink links
    private int sourceLinkID;
    private int sinkLinkID;

    //ID of origin and destination node IDs (unique)
    private int origNodeID; //presumably never used
    private int destNodeID;

    //set of node IDs associated with route
    private Set<Integer> routeNodeIDs;

    private double routeDistance;
    private double routeCricVelocity;

    //constructor
    public Route(String[] zSeq, double routeDistance) {
        zoneSeq = zSeq.clone();

        origZone = zSeq[0];
        destZone = zSeq[zSeq.length - 1];

        routeNodeIDs = new HashSet<Integer>();
        this.routeDistance = routeDistance;
    }

    public void setSourceLinkID(int linkID) {
        sourceLinkID = linkID;
    }

    public int getSourceLinkID() {
        return sourceLinkID;
    }

    public void setSinkLinkID(int linkID) {
        sinkLinkID = linkID;
    }

    public int getSinkLinkID() {
        return sinkLinkID;
    }

    public void setOrigNodeID(int nodeID) {
        origNodeID = nodeID;
    }

    public int getOrigNodeID() {
        return origNodeID;
    }

    public void setDestNodeID(int nodeID) {
        destNodeID = nodeID;
    }

    public int getDestNodeID() {
        return destNodeID;
    }

    public Set<Integer> getRouteNodes() {
        return routeNodeIDs;
    }

    public void addRouteNode(int nodeID) {
        routeNodeIDs.add(nodeID);
    }

    /**
     * @return the routeDistance
     */
    public double getRouteDistance() {
        return routeDistance;
    }

    /**
     * @param routeDistance the routeDistance to set
     */
    public void setRouteDistance(double routeDistance) {
        this.routeDistance = routeDistance;
    }

    /**
     * @return the routeCricVelocity
     */
    public double getRouteCricVelocity() {
        return routeCricVelocity;
    }

    /**
     * @param routeCricVelocity the routeCricVelocity to set
     */
    public void setRouteCricVelocity(double routeCricVelocity) {
        this.routeCricVelocity = routeCricVelocity;
    }
}
