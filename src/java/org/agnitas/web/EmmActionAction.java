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

package org.agnitas.web;

import org.agnitas.util.*;
import org.agnitas.actions.*;
import org.agnitas.dao.*;
import java.io.IOException;
import java.sql.*;
import java.util.*;
import javax.servlet.*;
import javax.servlet.http.*;
import org.apache.struts.action.*;
import org.apache.struts.util.*;
import org.apache.commons.beanutils.*;
import org.springframework.context.*;

/**
 * Implementation of <strong>Action</strong> that handles Targets
 *
 * @author Martin Helff
 */

public class EmmActionAction extends StrutsActionBase {
    
    public static final int ACTION_LIST = 1;
    
    public static final int ACTION_VIEW = 2;
    
    public static final int ACTION_SAVE = 4;
    
    public static final int ACTION_NEW = 6;
    
    public static final int ACTION_DELETE = 7;
    
    public static final int ACTION_CONFIRM_DELETE = 8;
    
    public static final int ACTION_ADD_MODULE = 9;
    
    // --------------------------------------------------------- Public Methods
    
    
    /**
     * Process the specified HTTP request, and create the corresponding HTTP
     * response (or forward to another web component that will create it).
     * Return an <code>ActionForward</code> instance describing where and how
     * control should be forwarded, or <code>null</code> if the response has
     * already been completed.
     * 
     * @param form 
     * @param req 
     * @param res 
     * @param mapping The ActionMapping used to select this instance
     * @exception IOException if an input/output error occurs
     * @exception ServletException if a servlet exception occurs
     * @return destination
     */
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest req,
            HttpServletResponse res)
            throws IOException, ServletException {
        
        EmmActionForm aForm=null;
        ActionMessages errors = new ActionMessages();
        ActionForward destination=null;
        
        if(!this.checkLogon(req)) {
            return mapping.findForward("logon");
        }
        
        aForm=(EmmActionForm)form;
        
        req.setAttribute("oplist", this.getActionOperations(req));
        AgnUtils.logger().info("Action: "+aForm.getAction()); 
        try {
            switch(aForm.getAction()) {
                case EmmActionAction.ACTION_LIST:
                    if(allowed("actions.show", req)) {
                        destination=mapping.findForward("list");
                    } else {
                        errors.add(ActionMessages.GLOBAL_MESSAGE, new ActionMessage("error.permissionDenied"));
                    }
                    break;
                    
                case EmmActionAction.ACTION_VIEW:
                    if(allowed("actions.show", req)) {
                        if(aForm.getActionID()!=0) {
                            aForm.setAction(EmmActionAction.ACTION_SAVE);
                            loadAction(aForm, req);
                        } else {
                            aForm.setAction(EmmActionAction.ACTION_NEW);
                        }
                        destination=mapping.findForward("success");
                    } else {
                        errors.add(ActionMessages.GLOBAL_MESSAGE, new ActionMessage("error.permissionDenied"));
                        destination=mapping.findForward("list");
                    }
                    break;
                    
                case EmmActionAction.ACTION_SAVE:
                    if(allowed("actions.change", req)) {
                        saveAction(aForm, req);
                    } else {
                        errors.add(ActionMessages.GLOBAL_MESSAGE, new ActionMessage("error.permissionDenied"));
                    }
                    destination=mapping.findForward("success");
                    break;
                    
                case EmmActionAction.ACTION_CONFIRM_DELETE:
                    loadAction(aForm, req);
                    destination=mapping.findForward("delete");
                    aForm.setAction(EmmActionAction.ACTION_DELETE);
                    break;
                    
                case EmmActionAction.ACTION_DELETE:
                    if(allowed("actions.delete", req)) {
                        deleteAction(aForm, req);
                    } else {
                        errors.add(ActionMessages.GLOBAL_MESSAGE, new ActionMessage("error.permissionDenied"));
                    }
                    aForm.setAction(EmmActionAction.ACTION_LIST);
                    destination=mapping.findForward("list");
                    break;
                    
                case EmmActionAction.ACTION_ADD_MODULE:
                    ActionOperation aMod=(ActionOperation) getBean(aForm.getNewModule());
                    ArrayList actions=aForm.getActions();
                    if(actions==null) {
                        actions=new ArrayList();
                    }
                    actions.add(aMod);
                    aForm.setActions(actions);
                    aForm.setAction(EmmActionAction.ACTION_SAVE);
                    destination=mapping.findForward("success");
                    break;
                    
                default:
                    destination=mapping.findForward("list");
                    break;
            }
            
        } catch (Exception e) {
            AgnUtils.logger().error("execute: "+e+"\n"+AgnUtils.getStackTrace(e));
            errors.add(ActionMessages.GLOBAL_MESSAGE, new ActionMessage("error.exception"));
        }
        
        // Report any errors we have discovered back to the original form
        if (!errors.isEmpty()) {
            saveErrors(req, errors);
            return (new ActionForward(mapping.getInput()));
        }
        
        return destination;
        
    }
    
    /**
     * Loads an action.
     */
    protected void loadAction(EmmActionForm aForm, HttpServletRequest req) throws Exception {
        
        EmmActionDao dao=(EmmActionDao) getBean("EmmActionDao");
        EmmAction aAction=dao.getEmmAction(aForm.getActionID(), getCompanyID(req));
        
        if(aAction!=null && aAction.getId()!=0) {
            aForm.setShortname(aAction.getShortname());
            aForm.setDescription(aAction.getDescription());
            aForm.setType(aAction.getType());
            aForm.setActions(aAction.getActions());
            AgnUtils.logger().info("loadAction: action "+aForm.getActionID()+" loaded");
        } else {
            AgnUtils.logger().warn("loadAction: could not load action "+aForm.getActionID());  
        }
        
        return;
    }
    
    /**
     * Saves an action.
     */
    protected void saveAction(EmmActionForm aForm, HttpServletRequest req) throws Exception {
        
        EmmAction aAction=(EmmAction) getBean("EmmAction");
        EmmActionDao dao=(EmmActionDao) getBean("EmmActionDao");
        
        aAction.setCompanyID(this.getCompanyID(req));
        aAction.setId(aForm.getActionID());
        aAction.setType(aForm.getType());
        aAction.setShortname(aForm.getShortname());
        aAction.setDescription(aForm.getDescription());
        aAction.setActions(aForm.getActions());
        
        aForm.setActionID(dao.saveEmmAction(aAction));
        
        return;
    }
    
    /**
     * Deletes an action.
     */
    protected void deleteAction(EmmActionForm aForm, HttpServletRequest req) {
        EmmActionDao dao=(EmmActionDao) getBean("EmmActionDao");
        
        dao.deleteEmmAction(aForm.getActionID(), this.getCompanyID(req));
        
        return;
    }
    
    /**
     * Gets action operations.
     */
    protected Map getActionOperations(HttpServletRequest req) {
        String name=null;
        String key=null;
        TreeMap ops=new TreeMap();
        ApplicationContext con=getWebApplicationContext();
        String[] names=con.getBeanNamesForType(org.agnitas.actions.ActionOperation.class);

        for(int i=0; i<names.length; i++) {
            name=names[i];
            if(allowed(new String("action.op."+name), req)) {
                key=this.getMessage(new String("action.op."+name), req);
                ops.put(key, name);
            }
        }
        
        return ops;
    }
}