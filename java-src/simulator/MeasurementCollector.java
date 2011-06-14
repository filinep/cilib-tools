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

import java.io.Closeable;
import java.util.List;
import net.sourceforge.cilib.algorithm.Algorithm;
import net.sourceforge.cilib.measurement.Measurement;

/**
 * Collect measurements from an {@code Algorithm}. This interface determines how
 * the measurements are collected from the running algorithm.
 */
interface MeasurementCollector extends Closeable {

    /**
     * Perform measurements on the provided {@code algorithm}.
     * @param algorithm The algorithm to perform the measurements on.
     */
    void measure(Algorithm algorithm);

    /**
     * Appends this measurement to the current list maintained by the collector.
     * @param measurement element to be added to the collector.
     */
    void add(Measurement<?> measurement);

    /**
     * Returns the textual descriptions of the collector's measurements.
     * <p>
     * The class names of the actual measurements are colelcted, placed
     * into a {@code List} and then returned.
     * @return the textual re[presentations of the measurements.
     */
    List<String> getDescriptions();
}
