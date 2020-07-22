# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger('__name__')

class AccountMove(models.Model):
    _inherit = 'account.move'    

    @api.depends('type')
    def _compute_invoice_filter_type_doc(self):

        ejecuta="no"
        if self.type=="in_invoice":
            tipo_doc="fc"
            typo="purchase"
            ejecuta="si"
        if self.type=="in_refund":
            tipo_doc="nc"
            typo="purchase"
            ejecuta="si"
        if self.type=="in_receipt":
            tipo_doc="nb"
            typo="purchase"
            ejecuta="si"

        if self.type=="out_invoice":
            tipo_doc="fc"
            typo="sale"
            ejecuta="si"
        if self.type=="out_refund":
            tipo_doc="nc"
            typo="sale"
            ejecuta="si"
        if self.type=="out_receipt":
            tipo_doc="nb"
            typo="sale"
            ejecuta="si"
        
        if ejecuta=="si":
            busca_diarios = self.env['account.journal'].search([('tipo_doc','=',tipo_doc),('type','=',typo)])
            for det in busca_diarios:
                idd=det.id
        else:
            idd=1
        self.invoice_filter_type_doc= idd


    invoice_filter_type_doc = fields.Char(compute='_compute_invoice_filter_type_doc')

    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    #default=invoice_filter_type_doc

    """journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('company_id', '=', company_id)]",
        default=_get_default_journal)"""