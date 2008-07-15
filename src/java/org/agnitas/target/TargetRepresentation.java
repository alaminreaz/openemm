/*********************************************************************************
 * The contents of this file are subject to the OpenEMM Public License Version 1.1
 * ("License"); You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at http://www.agnitas.org/openemm.
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License for
 * the specific language governing rights and limitations under the License.
 *
 * The Original Code is OpenEMM.
 * The Initial Developer of the Original Code is AGNITAS AG. Portions created by
 * AGNITAS AG are Copyright (C) 2006 AGNITAS AG. All Rights Reserved.
 *
 * All copies of the Covered Code must include on each user interface screen,
 * visible to all users at all times
 *    (a) the OpenEMM logo in the upper left corner and
 *    (b) the OpenEMM copyright notice at the very bottom center
 * See full license, exhibit B for requirements.
 ********************************************************************************/

package org.agnitas.target;

import java.io.Serializable;
import java.util.ArrayList;

/**
 *
 * @author mhe
 */
public interface TargetRepresentation extends Serializable {
    /**
     * Adds one node.
     */
    void addNode(TargetNode aNode);

    /**
     * Checks if all opened Brackes are closed.
     */
    boolean checkBracketBalance();

    /**
     * Removes one node.
     */
    boolean deleteNode(int index);

    /**
     * Generates bsh.
     */
    String generateBsh();

    /**
     * Generates sql statement.
     */
    String generateSQL();

    /**
     * Getter for allNodes.
     *
     * @return Value of allNodes.
     */
    ArrayList getAllNodes();

    /**
     * Setter for property node.
     * 
     * @param aNode New value of property node.
     */
    void setNode(int idx, TargetNode aNode);
    
}