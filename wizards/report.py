
import logging
import ast

from odoo import models, fields, api, _
from odoo.tools.misc import format_date

class BSAccountBankReconciliationReport(models.AbstractModel):
    _inherit = 'account.bank.reconciliation.report'

    @api.model
    def _get_templates(self):
        templates = super()._get_templates()
        templates['main_template'] = 'account_reports.bank_reconciliation_report_main_template'
        templates['search_template'] = 'account_reports.search_template'
        return templates