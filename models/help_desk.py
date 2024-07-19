from odoo import api, fields, models, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    partner_bank = fields.Char('Partner Bank',help="This bank account used for refund")

    def name_get(self):
        result = []
        for ticket in self:
            result.append((ticket.id, "%s (#%s)" % (ticket.name, 'BST'+str(ticket._origin.id))))
        return result