# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger('__name__')

class AccountMove(models.Model):
    _inherit = 'account.move'

    isrl_ret_id = fields.Many2one('isrl.retention', string='ISLR', copy=False, help='ISLR')

    # Main Function
    def action_post(self):
        super().action_post()
        bann=0
        bann=self.verifica_exento_islr()
        if bann>0:
            self.create_retention()

    def create_retention(self):
        if self.type in ('in_invoice','out_invoice'):
            if self.isrl_ret_id.id:
                pass
            else: 
                if self.partner_id.people_type :
                    self.isrl_ret_id = self.env['isrl.retention'].create({
                        'invoice_id': self.id,
                        'partner_id': self.partner_id.id,
                    })
                    for item in self.invoice_line_ids:
                        if item.concept_isrl_id:
                            for rate in item.concept_isrl_id.rate_ids:
                                if self.partner_id.people_type == rate.people_type and  item.price_subtotal > rate.min  :
                                    base = item.price_subtotal * (rate.subtotal / 100)
                                    subtotal =  base * (rate.retention_percentage / 100)
                                    self.vat_isrl_line_id = self.env['isrl.retention.invoice.line'].create({
                                        'name': item.concept_isrl_id.id,
                                        'code':rate.code,
                                        'retention_id': self.isrl_ret_id.id,
                                        'cantidad': rate.retention_percentage,
                                        'base': base,
                                        'retention': subtotal,
                                        'sustraendo': rate.subtract,
                                        'total': subtotal - rate.subtract
                                    })
                else :
                    raise UserError("the Partner does not have identified the type of person.")

        if self.type =='in_invoice':
            self.isrl_ret_id.action_post()

    def verifica_exento_islr(self):
        acum=0
        #raise UserError(_('self = %s')%self.id)
        puntero_move_line = self.env['account.move.line'].search([('move_id','=',self.id),('account_internal_type','=','other')])
        for det_puntero in puntero_move_line:
            if det_puntero.product_id.product_tmpl_id.concept_isrl_id.id:
                acum=acum+1
        #raise UserError(_('acum: %s ')%acum)
        return acum
