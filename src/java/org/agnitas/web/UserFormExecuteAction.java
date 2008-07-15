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
import org.agnitas.beans.*;
import org.agnitas.dao.*;
import java.io.*;
import java.util.*;
import javax.servlet.*;
import javax.servlet.http.*;
import org.apache.struts.action.*;


/**
 * Implementation of <strong>Action</strong> that processes a form.do request
 *
 * @author mhe
 * @version $Revision: 2.5 $ $Date: 2006/07/11 11:48:03 $
 */

public final class UserFormExecuteAction extends StrutsActionBase {
    
    // --------------------------------------------------------- Public Methods
    TimeoutLRUMap companys=new TimeoutLRUMap(AgnUtils.getDefaultIntValue("onepixel.keys.maxCache"), AgnUtils.getDefaultIntValue("onepixel.keys.maxCacheTimeMillis"));
    
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
     * @return the action to forward to. 
     */
    public ActionForward execute(ActionMapping mapping,
            ActionForm form,
            HttpServletRequest req,
            HttpServletResponse res)
            throws IOException, ServletException {
        
        // Validate the request parameters specified by the user
        ActionMessages errors = new ActionMessages();
        UserFormExecuteForm aForm=(UserFormExecuteForm)form;
        ActionForward destination=null;
        HashMap params=new HashMap();
        boolean endAction=false;
        
        try {
            this.processUID(req, params, aForm.getAgnUseSession());
            params.put("requestParameters", AgnUtils.getReqParameters(req));
            params.put("_request", req);
            
            String responseContent=executeForm(aForm, params, req, errors);
            if(params.get("responseRedirect")!=null) {
                res.sendRedirect((String)params.get("responseRedirect"));
            } else {
                String responseMimetype=new String("text/html");
                if(params.get("responseMimetype")!=null) {
                    responseMimetype=(String)params.get("responseMimetype");
                }
                res.setContentType(responseMimetype);
                
                PrintWriter out=res.getWriter();
                out.print(responseContent);
                out.flush();
                out.close();
                
                res.flushBuffer();
            }
            if(params.get("_error")==null) {
                endAction=this.evaluateFormEndAction(aForm, params);
            }
        } catch (Exception e) {
            AgnUtils.logger().error("execute: "+e+"\n"+AgnUtils.getStackTrace(e));
            errors.add(ActionMessages.GLOBAL_MESSAGE, new ActionMessage("error.exception"));
        }
        
        // Report any errors we have discovered back to the original form
        if (!errors.isEmpty()) {
            saveErrors(req, errors);
            return new ActionForward(mapping.getInput());
        }
        
        return destination;
        
    }

    /** Execute the requested form.
     * Reads the form defined by aForm.getAgnFN() and aForm.getAgnCI() from the
     * database and executes it.
     * @param aForm form info.
     * @param params a map containing the form values.
     * @param req the ServletRequest, used to get the ApplicationContext.
     * @param errors used to sotre error descriptions.
     */  
    protected String executeForm(UserFormExecuteForm aForm, HashMap params, HttpServletRequest req, ActionMessages errors) throws IOException {
        
        String result=new String("no parameters");
        boolean status;
        
        UserFormDao dao=(UserFormDao) getBean("UserFormDao");
        UserForm aUserForm=dao.getUserFormByName(aForm.getAgnFN(), aForm.getAgnCI());
        
        if(aUserForm!=null) {
            result=aUserForm.evaluateForm(this.getWebApplicationContext(), params);
        } else {
            return "form not found";
        }
        
        return result;
    }
    
    /** Execute the end action of the requested form.
     * Reads the form defined by aForm.getAgnFN() and aForm.getAgnCI() from the
     * database and executes it's end action.
     * @param aForm form info.
     * @param params a map containing the form values.
     */  
    protected boolean evaluateFormEndAction(UserFormExecuteForm aForm, HashMap params) throws IOException {
        
        UserFormDao dao=(UserFormDao) getBean("UserFormDao");
        UserForm aUserForm=dao.getUserFormByName(aForm.getAgnFN(), aForm.getAgnCI());
        
        if(aUserForm!=null || aUserForm.getEndActionID()==0) {
            return false;
        }
        
        return aUserForm.evaluateEndAction(this.getWebApplicationContext(), params);
    }
   
    /** Retrieves information from a given url. 
     * Parses an url and returns the retrieved values in a hash.
     * @param req ServletRequest, used to get the Session.
     * @param params HashMap to store the retrieved values in.
     * @param useSession also store the result in the session if this is not 0.
     */ 
    public void processUID(HttpServletRequest req, HashMap params, int useSession) {
        UID uid=null;
        String par=req.getParameter("agnUID");

        if(par!=null) {
            uid=this.decodeTagString(par);
        }
        
        if(uid!=null) {
            params.put("customerID", new Integer((int)uid.getCustomerID()));
            params.put("mailingID", new Integer((int)uid.getMailingID()));
            params.put("urlID", new Integer((int)uid.getURLID()));
            params.put("agnUID", par);
            if(useSession!=0) {
                HashMap tmpPars=new HashMap();
                tmpPars.putAll(params);
                req.getSession().setAttribute("agnFormParams", tmpPars);
                params.put("sessionID", req.getSession().getId());
            }
        } else {
            if(useSession!=0) {
                if(req.getSession().getAttribute("agnFormParams")!=null){
                    params.putAll((HashMap)req.getSession().getAttribute("agnFormParams"));
                }
            }
        }
    }
   
    /** Use a tag to get a UID.
     * Retrieves a UID according to a given tag.
     * @param tag a string defining the uid.
     * @return the resulting UID.
     */
    public UID decodeTagString(String tag) {
        boolean exitValue=true;
        
        String passphrase=null;
        int companyID=0;
        Company company=null;
        UID uid=null;
        
        try {
            uid = (UID) getBean("UID");
            
            uid.parseUID(tag);
            companyID=(int)uid.getCompanyID();
            if(companyID==0) {
                return null;
            }
            
            if(companys!=null) {
                company=(Company)companys.get(Integer.toString(companyID));
            }
            
            if(company==null) {
                CompanyDao dao=(CompanyDao) getBean("CompanyDao");
                
                company=dao.getCompany(companyID);
            }
            
            if(company!=null) {
                uid.setPassword(company.getSecret());
                
                exitValue=uid.validateUID();
                if(!exitValue) {
                    uid=null;
                }
            }
            
        } catch (Exception e) {
            AgnUtils.logger().error("decodeTagString: " + e);
            return null;
        }
        
        
        return uid;
    }
}