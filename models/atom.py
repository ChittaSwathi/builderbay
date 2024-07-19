# -*- coding: utf-8 -*-
# Part of build suvidha. See LICENSE file for full copyright and licensing details.

import base64
import datetime
from datetime import datetime
import hashlib
import hmac
import logging
from odoo.http import request
from werkzeug import urls
import xml
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare
import requests

_logger = logging.getLogger(__name__)


class BSPaymentAcquirerAtom(models.Model):
    _inherit = 'payment.acquirer'
    
    prod_atom_url = fields.Char(string='Atom Production Url', groups='base.group_user', help="This url will connect to atom production server")
    test_atom_url = fields.Char(string='Atom Test Url', groups='base.group_user', help="This url will connect to atom test server")

    @api.model
    def _atom_requery(self):

        AtomAcqRec = self.env.ref('payment_atom.payment_acquirer_atom')

        if request.env.user.partner_id.customer_type == 'b2b':
            AtomLoginID = AtomAcqRec.atom_b2b_login_id
            HashReqkey = AtomAcqRec.b2b_hash_request_key
        else:
            AtomLoginID = AtomAcqRec.atom_b2c_login_id
            HashReqkey = AtomAcqRec.b2c_hash_request_key
        key_bytes = bytes(str(HashReqkey), 'UTF-8')
        ToCheckTranxs = self.env['payment.transaction'].search([('state','not in',['draft','done']),
                                                                ('state_message','!=','success'),
                                                                ('acquirer_reference','!=',''),
                                                                ('acquirer_id','!=',''),('to_skip','=',False)])
        for pending_trans in ToCheckTranxs:
            checksum_string = ('merchantid=%s&merchanttxnid=%s&amt=%.2f&tdate=%s')%(AtomLoginID,
                                                              pending_trans.reference,
                                                              pending_trans.amount,
                                                              pending_trans.date.date())
            
            if self.state == 'enabled':
                url = AtomAcqRec.prod_atom_url
                data_bytes = bytes(checksum_string, 'UTF-8')
                shasign_check = hmac.new(key_bytes, data_bytes, hashlib.sha512).hexdigest()
                url = url+shasign_check
                response = requests.post(url)
                print(url, response.json)
                json_res = response.json
                status = json_res.get('Verified')
                statusCode = json_res.get('StatusCode')
                if status == 'SUCCESS' and statusCode == '001':
                    pending_trans._set_transaction_done()
                if status in ['FAILED','Invalid Data','Invalid date format'] and statusCode in ['002','005','006']:
                    pending_trans.to_skip = True
                pending_trans.write({'detailed_response': str(pending_trans.detailed_response) + '***************' + str(json_res)})
            else:
                url = AtomAcqRec.test_atom_url
#                 data_bytes = bytes(checksum_string, 'UTF-8')
#                 shasign_check = hmac.new(key_bytes, data_bytes, hashlib.sha512).hexdigest()
                url = url+checksum_string
                print(url)
                response = requests.post(url)
                print(url, response.content)
                string_xml = response.content
                tree = xml.etree.ElementTree.fromstring(string_xml)
                Resp = {}
                for ky in tree.keys(): Resp.update({ky: tree.attrib[ky]})
                pending_trans.write({'detailed_response': str(pending_trans.detailed_response) + '***************' + str(Resp)})

        return True