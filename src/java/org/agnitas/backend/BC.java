/*********************************************************************************
 * The contents of this file are subject to the Common Public Attribution
 * License Version 1.0 (the "License"); you may not use this file except in
 * compliance with the License. You may obtain a copy of the License at
 * http://www.openemm.org/cpal1.html. The License is based on the Mozilla
 * Public License Version 1.1 but Sections 14 and 15 have been added to cover
 * use of software over a computer network and provide for limited attribution
 * for the Original Developer. In addition, Exhibit A has been modified to be
 * consistent with Exhibit B.
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
 * the specific language governing rights and limitations under the License.
 *
 * The Original Code is OpenEMM.
 * The Original Developer is the Initial Developer.
 * The Initial Developer of the Original Code is AGNITAS AG. All portions of
 * the code written by AGNITAS AG are Copyright (c) 2007 AGNITAS AG. All Rights
 * Reserved.
 *
 * Contributor(s): AGNITAS AG.
 ********************************************************************************/
package org.agnitas.backend;

import  java.util.Vector;
import  java.util.Hashtable;
import  java.sql.ResultSet;
import  org.agnitas.util.Log;

public class BC {
    /** local reference to context */
    private Data        data = null;
    /** temporary table for storing customerIDs */
    protected String    table = null;
    /** if the table had been successful created */
    protected boolean   tableCreated = false;
    /** columns found in temporary table */
    private Vector      columns = null;
    /** mapping to columns in original tables */
    private Hashtable   cmap = null;
    /** type of columns */
    private Hashtable   tmap = null;
    /* parts of final where clause */
    protected String    partFrom = null;
    protected String    partCombine = null;
    protected String    partUserstatus = null;
    protected String    partUsertype = null;
    protected String    partMailinglist = null;
    protected String    partSubselect = null;
    protected String    partSelect = null;
    protected String    partCounter = null;
    protected String    fixedClause = null;
    /** number of real receivers for this mailing */
    protected long      count = 0;

    public BC () {
    }

    public void setData (Object datap) {
        data = (Data) datap;
    }

    protected boolean removeTable (String tname) {
        boolean rc = false;

        try {
            data.dbase.execUpdate ("TRUNCATE TABLE " + tname);
        } catch (Exception e) {
            data.logging (Log.WARNING, "bc", "Failed to truncate table " + tname + ": " + e.toString ());
        }
        try {
            data.dbase.execUpdate ("DROP TABLE " + tname);
            rc = true;
        } catch (Exception e) {
            data.logging (Log.ERROR, "bc", "Failed to drop table " + tname + ": " + e.toString ());
        }
        return rc;
    }

    protected boolean createTable (String tname, String stmt) {
        boolean rc = false;

        for (int n = 0; (! rc) && (n < 2); ++n) {
            try {
                data.dbase.execUpdate (stmt);
                rc = true;
            } catch (Exception e) {
                data.logging (n == 0 ? Log.WARNING : Log.ERROR, "bc", "Failed to create table " + tname + ": " + e.toString ());
                if (n == 0) {
                    removeTable (tname);
                }
            }
        }
        return rc;
    }

    public void done () {
        if (tableCreated && removeTable (table)) {
            tableCreated = false;
        }
    }

    public void getColumns (Vector collect, Hashtable cmap, Hashtable tmap) {
        collect.add ("customer_id");
        cmap.put ("customer_id", "cust.customer_id");
        tmap.put ("customer_id", "int");
        collect.add ("user_type");
        cmap.put ("user_type", "bind.user_type");
        tmap.put ("user_type", "varchar(1)");
        collect.add ("mediatype");
        cmap.put ("mediatype", "bind.mediatype");
        tmap.put ("mediatype", "int");
    }

    public void getRestrictions (Vector collect) {
        collect.add (partSubselect);
    }

    public void getExtensions (Vector collect) {
    }

    public void createTable () {
        table = "TMP_CRT_" + data.status_field + "_" + data.mailing_id + "_" + data.maildrop_status_id + "_TBL";
        columns = new Vector ();
        cmap = new Hashtable ();
        tmap = new Hashtable ();
        getColumns (columns, cmap, tmap);
        String  tfields = "";
        String  sfields = "";
        for (int n = 0; n < columns.size (); ++n) {
            String  sep = (n == 0 ? "" : ", ");
            String  col = (String) columns.get (n);
            String  type = (String) tmap.get (col);
            String  sel = (String) cmap.get (col);

            tfields += sep + col;
            if (type != null)
                tfields += " " + type;
            sfields += sep + (sel != null ? sel : col);
        }

        partSelect = partCombine + " AND ((" + partUserstatus + " AND " + partMailinglist;
        partCounter = partCombine + " AND (" + partUserstatus + " AND " + partMailinglist;
        if (partUsertype != null) {
            partSelect += " AND " + partUsertype;
        }
        Vector  collect = new Vector ();
        boolean limitSelect = data.isWorldMailing () || data.isOnDemandMailing () || data.isRuleMailing () || (data.isCampaignMailing () && (data.campaignTransactionID > 0));

        getRestrictions (collect);
        for (int n = 0; n < collect.size (); ++n) {
            String  rest = (String) collect.get (n);
            if (rest != null) {
                if (limitSelect) {
                    partSelect += " AND (" + rest + ")";
                }
                partCounter += " AND (" + rest + ")";
            }
        }
        partSelect += ")";
        partCounter += ")";
        collect.clear ();
        getExtensions (collect);
        for (int n = 0; n < collect.size (); ++n) {
            String  ext = (String) collect.get (n);
            if (ext != null) {
                partSelect += " OR (" + ext + ")";
            }
        }
        partSelect += ")";
        String  stmt =
            "CREATE TABLE " + table + " (" + tfields + ") AS SELECT " + sfields +
            " FROM " + partFrom + " WHERE " + partSelect;
        tableCreated = createTable (table, stmt);
    }

    protected String partCustomer (String prefix) {
        if (prefix == null)
            prefix = "";
        else
            prefix += ".";
        if (data.isCampaignMailing () && (data.campaignTransactionID == 0)) {
            return prefix + "customer_id = " + data.campaignCustomerID;
        } else if (data.isPreviewMailing ()) {
            return prefix + "customer_id = " + data.previewCustomerID;
        }
        return null;
    }

    protected String partClause (String query) {
        if (query != null)
            return fixedClause + " AND (" + query + ")";
        return fixedClause;
    }

    public boolean prepareClause () {
        boolean rc;

        partFrom = "customer_" + data.company_id + "_tbl cust, customer_" + data.company_id + "_binding_tbl bind";
        partCombine = "cust.customer_id = bind.customer_id";
        partUserstatus = "bind.user_status = " + data.defaultUserStatus;
        partMailinglist = "bind.mailinglist_id = " + data.mailinglist_id;
        if (data.isAdminMailing () ||
            data.isTestMailing () ||
            data.isRuleMailing () ||
            data.isOnDemandMailing () ||
            data.isWorldMailing () ||
            (data.isCampaignMailing () && (data.campaignTransactionID > 0))) {
            partSubselect = data.subselect;
            if (data.isCampaignMailing ()) {
                String  tselect = "cust.transaction_id = " + data.campaignTransactionID;
                if (partSubselect == null) {
                    partSubselect = tselect;
                } else {
                    partSubselect = "(" + partSubselect + ") AND " + tselect;
                }
            }
            if (data.isAdminMailing ()) {
                partUsertype = "bind.user_type = 'A'";
            } else if (data.isTestMailing ()) {
                partUsertype = "bind.user_type IN ('A', 'T')";
            }
            createTable ();
            rc = tableCreated;
            if (rc) {
                String  query;

                if (data.isAdminMailing () || data.isTestMailing ()) {
                    query = "SELECT count(cust.customer_id) FROM " + partFrom + " WHERE " + partCounter;
                } else {
                    query = "SELECT count(distinct customer_id) FROM " + table + " WHERE user_type IN ('A', 'T', 'W')";
                }
                try {
                    ResultSet   rset = data.dbase.execQuery (query);

                    if (rset.next ()) {
                        count = rset.getLong (1);
                    }
                    rset.close ();
                } catch (Exception e) {
                    data.logging (Log.ERROR, "bc", "Failed to count " + table + ": " + e.toString ());
                }
            }
            partFrom = "customer_" + data.company_id + "_tbl cust, " + table + " bind";
        } else if (data.isCampaignMailing () || data.isPreviewMailing ()) {
            if (data.isCampaignMailing ()) {
                if (data.defaultUserStatus != data.campaignUserStatus) {
                    partUserstatus = "bind.user_status IN (" + data.defaultUserStatus + ", " + data.campaignUserStatus + ")";
                }
            }
            rc = true;
            count = 1;
        } else
            rc = false;
        fixedClause = "FROM " + partFrom + " WHERE " + partCombine;
        return rc;
    }

    public long subscriber () {
        return count;
    }

    public Vector createClauses () {
        Vector  rc = new Vector ();

        if (data.isWorldMailing ()) {
            rc.add (partClause ("bind.user_type IN ('A', 'T')"));
            rc.add (partClause ("bind.user_type = 'W'"));
        } else if (data.isAdminMailing () || data.isTestMailing () || data.isRuleMailing () || (data.isOnDemandMailing ()) || (data.isCampaignMailing () && (data.campaignTransactionID > 0))) {
            if (data.isRuleMailing () || data.isOnDemandMailing ()) {
                rc.add (null);
            }
            rc.add (partClause (null));
        } else if (data.isCampaignMailing () || data.isPreviewMailing ()) {
            rc.add (partClause (partCustomer ("cust")));
        }
        return rc;
    }

    public String createClause () {
        String  rc;

        if (data.isWorldMailing () ||
            data.isAdminMailing () ||
            data.isTestMailing () ||
            data.isRuleMailing () ||
            (data.isOnDemandMailing ()) ||
            (data.isCampaignMailing () && (data.campaignTransactionID > 0))) {
            rc = partClause (null);
        } else if (data.isCampaignMailing () || data.isPreviewMailing ()) {
            rc = partClause (partCustomer ("cust"));
        } else
            rc = null;
        return rc;
    }

    public String mailtrackStatement (String destination) {
        return "INSERT INTO " + destination + " (company_id, status_id, mailing_id, customer_id) " +
            "SELECT " + data.company_id + ", " + data.maildrop_status_id + ", " + data.mailing_id + ", customer_id " +
            "FROM " + table;
    }
}
