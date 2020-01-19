/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package anisopedctm;

import java.util.ArrayList;

import anisopedctm.Board;


/*
 * @author Flurin Haenseler, Gael Lederrey
 * 
 * @version StochasticAnisoPedCTM v1.0
 * @author Shubhankar Mathur
 * 
 */

public class AnisoPedCTM {
	
	public static void main(String[] args) {

		/*
		 * Experiments
		 */
		ArrayList<String> expList = new ArrayList<String>();
		
                expList.add("examples/scenarios/SYD350-01-SbFD_scenario.txt");
                expList.add("examples/scenarios/SYD350-02-SbFD_scenario.txt");
                expList.add("examples/scenarios/SYD350-01-weidmann_scenario.txt");
                
		expList.parallelStream().forEach((exp) -> {
			
			//initialize simulation by generating board
			Board board = new Board(exp);
			
			//simulate
			board.simulate();
			
		});
		
                
	}

}

