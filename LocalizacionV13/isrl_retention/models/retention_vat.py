# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

_logger = logging.getLogger('__name__')


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    concept_isrl_id = fields.Many2one('islr.concept', string='ISRL Concept')


class InvoiceLineInherit(models.Model):
    _inherit = 'account.move.line'

    concept_isrl_id = fields.Many2one(related='product_id.product_tmpl_id.concept_isrl_id', string='ISRL Concepto')
    vat_isrl_line_id = fields.Many2one('isrl.retention.invoice.linet', string='ISRL Line')


class VatRetentionInvoiceLine(models.Model):
    """This model is for a line invoices withholed."""
    _name = 'isrl.retention.invoice.line'

    name = fields.Many2one('islr.concept', string='ISRL Concept')
    code = fields.Char( string='Código')
    retention_id = fields.Many2one('isrl.retention', string='Vat retention')
    cantidad = fields.Float(string='Cantidad Porcentual')
    base = fields.Float(string='Base')
    retention = fields.Float(string='Retención')
    sustraendo = fields.Float(string='Sustraendo')
    total = fields.Float(string='ISRL Amount retention')
    
class RetentionVat(models.Model):
    """This is a main model for rentetion vat control."""
    _name = 'isrl.retention'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Comprobante  Número', default='0000-00-00')
    move_id = fields.Many2one('account.move', string='Asiento Contable')
    
    type = fields.Selection(related='invoice_id.type',)
    
    date_move = fields.Date(string='Date Move',default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_isrl = fields.Date(string='Date ISRL',default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    partner_id = fields.Many2one(comodel_name='res.partner', string='Empresa')
    invoice_id = fields.Many2one(comodel_name='account.move', string='Factura')
    
    lines_id = fields.One2many(comodel_name='isrl.retention.invoice.line', inverse_name='retention_id', string='Lines')
    
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),], string='State', readonly=True, default='draft')

    def doc_cedula(self,aux):
        #nro_doc=self.partner_id.vat
        busca_partner = self.env['res.partner'].search([('id','=',aux)])
        for det in busca_partner:
            tipo_doc=busca_partner.doc_type
            nro_doc=str(busca_partner.vat)
        nro_doc=nro_doc.replace('V','')
        nro_doc=nro_doc.replace('v','')
        nro_doc=nro_doc.replace('E','')
        nro_doc=nro_doc.replace('e','')
        nro_doc=nro_doc.replace('G','')
        nro_doc=nro_doc.replace('g','')
        nro_doc=nro_doc.replace('J','')
        nro_doc=nro_doc.replace('j','')
        nro_doc=nro_doc.replace('P','')
        nro_doc=nro_doc.replace('p','')
        nro_doc=nro_doc.replace('-','')
        
        if tipo_doc=="v":
            tipo_doc="V"
        if tipo_doc=="e":
            tipo_doc="E"
        if tipo_doc=="g":
            tipo_doc="G"
        if tipo_doc=="j":
            tipo_doc="J"
        if tipo_doc=="p":
            tipo_doc="P"
        resultado=str(tipo_doc)+"-"+str(nro_doc)
        return resultado
        #raise UserError(_('cedula: %s')%resultado)
        
    def action_post(self):
        customer = ('out_invoice','out_refund','out_receipt')
        vendor   = ('in_invoice','in_refund','in_receipt')
        name_asiento = self.env['ir.sequence'].next_by_code('purchase.isrl.retention.account')
        if self.invoice_id.company_id.partner_id.sale_isrl_id.id:
            self.move_id =  self.env['account.move'].create({
                'type': 'entry',
                'isrl_ret_id': self.id,
                'name': name_asiento,
                'ref': "Retención del %s %% ISRL de la Factura %s" % (self.partner_id.name,self.invoice_id.name),
                'journal_id' :self.invoice_id.company_id.partner_id.sale_isrl_id.id
            })
            if self.type in customer:
                value = {
                    'name': name_asiento,
                    'ref': "Retención del %s %% ISRL de la Factura %s" % (self.partner_id.name,self.invoice_id.name),
                    'move_id':  self.move_id.id,
                    'date': self.date_move,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_id.company_id.partner_id.property_account_receivable_id.id, 
                    'credit': self.vat_retentioned,
                    'debit': 0.0,
                    'balance':-self.vat_retentioned, # signo negativo
                    'price_unit':self.vat_retentioned,
                    'price_subtotal':self.vat_retentioned,
                    'price_total':self.vat_retentioned,
                }

                self.env['account.move.line'].create(value)

                value = {
                    'name': name_asiento,
                    'ref': "Retención del %s %% ISRL de la Factura %s" % (self.partner_id.name,self.invoice_id.name),
                    'move_id':  self.move_id.id,
                    'date': self.date_move,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_id.company_id.partner_id.account_isrl_receivable_id.id,
                    'credit':  0.0,
                    'debit': self.vat_retentioned, # aqi va cero   EL DEBITO CUNDO TIENE VALOR, ES QUE EN ACCOUNT_MOVE TOMA UN VALOR
                    'balance':-self.vat_retentioned, # signo negativo
                    'price_unit':self.vat_retentioned,
                    'price_subtotal':self.vat_retentioned,
                    'price_total':self.vat_retentioned,
                }

                self.env['account.move.line'].create(value)
            else :
                self.name = self.env['ir.sequence'].next_by_code('purchase.isrl.retention.voucher.number') 
                value = {
                    'name': name_asiento,
                    'ref': "Retención del %s %% ISRL de la Factura %s" % (self.partner_id.name,self.invoice_id.name),
                    'move_id':  self.move_id.id,
                    'date': self.date_move,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_id.company_id.partner_id.property_account_payable_id.id, 
                    'credit': 0.0,
                    'debit': self.vat_retentioned,
                    'balance':-self.vat_retentioned, # signo negativo
                    'price_unit':self.vat_retentioned,
                    'price_subtotal':self.vat_retentioned,
                    'price_total':self.vat_retentioned,
                }

                self.env['account.move.line'].create(value)

                value = {
                    'name': name_asiento,
                    'ref': "Retención del %s %% ISRL de la Factura %s" % (self.partner_id.name,self.invoice_id.name),
                    'move_id':  self.move_id.id,
                    'date': self.date_move,
                    'partner_id': self.partner_id.id,
                    'account_id': self.invoice_id.company_id.partner_id.account_isrl_payable_id.id,
                    'credit': self.vat_retentioned,
                    'debit':  0.0, # aqi va cero   EL DEBITO CUNDO TIENE VALOR, ES QUE EN ACCOUNT_MOVE TOMA UN VALOR
                    'balance':-self.vat_retentioned, # signo negativo
                    'price_unit':self.vat_retentioned,
                    'price_subtotal':self.vat_retentioned,
                    'price_total':self.vat_retentioned,
                }
                self.env['account.move.line'].create(value)

            self.state =  'done' 
            self.move_id.action_post()
        else :
            raise UserError("Configure el Diario en la compañia")
    
    def formato_fecha2(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result
    def get_address_partner(self):
        location = ''
        streets = ''
        if self.partner_id:
            location = self._get_state_and_city()
            streets = self._get_streets()
        return (streets + " " + location)


    def _get_state_and_city(self):
        state = ''
        city = ''
        if self.partner_id.state_id:
            state = "Edo." + " " + str(self.partner_id.state_id.name or '')
            _logger.info("\n\n\n state %s \n\n\n", state)
        if self.partner_id.city:
            city = str(self.partner_id.city or '')
            # _logger.info("\n\n\n city %s\n\n\n", city)
        result = city + " " + state
        _logger.info("\n\n\n result %s \n\n\n", result)
        return  result 


    def _get_streets(self):
        street2 = ''
        av = ''
        if self.partner_id.street:
            av = str(self.partner_id.street or '')
        if self.partner_id.street2:
            street2 = str(self.partner_id.street2 or '')
        result = av + " " + street2
        return result

    def get_company_address(self):
        location = ''
        streets = ''
        if self.invoice_id.company_id:
            streets = self._get_company_street()
            location = self._get_company_state_city()
        _logger.info("\n\n\n street %s location %s\n\n\n", streets, location)
        return  (streets + " " + location)


    def _get_company_street(self):
        street2 = ''
        av = ''
        if self.invoice_id.company_id.street:
            av = str(self.invoice_id.company_id.street or '')
        if self.invoice_id.company_id.street2:
            street2 = str(self.invoice_id.company_id.street2 or '')
        result = av + " " + street2
        return result


    def _get_company_state_city(self):
        state = ''
        city = ''
        if self.invoice_id.company_id.state_id:
            state = "Edo." + " " + str(self.invoice_id.company_id.state_id.name or '')
            _logger.info("\n\n\n state %s \n\n\n", state)
        if self.invoice_id.company_id.city:
            city = str(self.invoice_id.company_id.city or '')
            _logger.info("\n\n\n city %s\n\n\n", city)
        result = city + " " + state
        _logger.info("\n\n\n result %s \n\n\n", result)
        return  result

    @api.model
    def _compute_amount_untaxed(self):
        for item in self:
            item.amount_untaxed = 0 
            for line in item.lines_id:
                item.amount_untaxed += line.base

    @api.model
    def _compute_vat_retentioned(self):
        for item in self :
            item.vat_retentioned = 0 
            for line in item.lines_id :
                item.vat_retentioned += line.total

    amount_untaxed = fields.Float(string='Base Imponible',compute='_compute_amount_untaxed')
    vat_retentioned = fields.Float(string='ISRl retenido',compute='_compute_vat_retentioned')
    
    
