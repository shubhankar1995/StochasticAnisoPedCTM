package anisopedctm;

/**
 * Blockage class
 * 
 * @version StochasticAnisoPedCTM v1.0
 * @author Shubhankar Mathur
 *
 */

public class Blockage {
	private String cell; 
	private int startTime;
	private int endTime;
	private double blockagePercent;
	
	public Blockage(String cell, int startTime, int endTime, double blockagePercent) {
		
		this.cell = cell;
		this.startTime = startTime;
		this.endTime = endTime;
		this.blockagePercent = blockagePercent;
	}

	public String getCell() {
		return cell;
	}

	public double getStartTime() {
		return startTime;
	}

	public double getEndTime() {
		return endTime;
	}

	public double getBlockagePercent() {
		return blockagePercent;
	}
	
	
	
}