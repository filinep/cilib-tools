/**
 * Computational Intelligence Library (CIlib)
 * Copyright (C) 2003 - 2010
 * Computational Intelligence Research Group (CIRG@UP)
 * Department of Computer Science
 * University of Pretoria
 * South Africa
 *
 * This library is free software; you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library; if not, see <http://www.gnu.org/licenses/>.
 */
package simulator;

import com.google.inject.Guice;
import com.google.inject.Injector;
import java.io.File;
import java.util.List;
import net.sourceforge.cilib.algorithm.ProgressListener;

/**
 * This is the entry point for the CIlib simulator. This class accepts one
 * command line parameter, which is the name of the XML config file to parse.
 *
 * @author  Edwin Peer
 */
public final class Main {

    private Main() {} // Prevent instances of this class.

    /**
     * Main entry point for the simulator.
     * @param args provided arguments.
     */
    public static void main(String[] args) {
        if (args.length < 1) {
            throw new IllegalArgumentException("Please provide the correct arguments.\nUsage: Simulator <simulation-config.xml>");
        }

        int cpus;
        if(args.length > 1) {
            cpus = Integer.parseInt(args[1]);
        } else {
            cpus = Runtime.getRuntime().availableProcessors();
        }

        SimulatorShell shell = new SimulatorShell(new XMLObjectBuilder(), cpus);
        final List<Simulator> simulators = shell.prepare(new File(args[0]));

        shell.execute(simulators, new ProgressText(simulators.size()));
    }
}
