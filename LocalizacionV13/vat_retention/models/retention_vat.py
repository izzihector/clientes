# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger('__name__')



class InvoiceLineInherit(models.Model):
    _inherit = 'account.move.line'

    retention_id = fields.Many2one('vat.retention', string='VAT Retention')


class VatRetentionTaxLines(models.Model):
    """This model is about tax withheld in a invoice."""
    _name = 'vat.retention.tax.lines'

    name = fields.Char(string='Tax name', size=40)
    tax_id = fields.Many2one('account.tax', string="Tax")
    company_id = fields.Many2one('res.company', string='Company')
    vat_ret_line_id = fields.Many2one('vat.retention.invoice.line', ondelete="cascade",string='vat_ret_line_id')
    base_tax = fields.Float(string='Base tax')
    tax_amount = fields.Float(string='Tax amount')
    amount_withheld = fields.Float(string='Amount withheld')



class VatRetentionInvoiceLine(models.Model):
    """This model is for a line invoices withholed."""
    _name = 'vat.retention.invoice.line'


 

    #@api.depends('amount_vat_ret', 'retention_rate')
    def _compute_amount_withheld(self):
        return 0
        """This function compute the VAT retention."""
        #amount = (self.amount_vat_ret * self.retention_rate) / 100
        #_logger.info('\n\n\n amount %s \n\n\n', amount)
        #self.retention_amount = amount
        #voucher = self.env['vat.retention'].search([('id', '=', self.retention_id.id)])
        #_logger.info("\n\n\n voucher %s\n\n\n",voucher)
        #voucher.vat_retentioned = amount
    


    name = fields.Char(string='Description')
    retention_id = fields.Many2one('vat.retention', string='Vat retention')
    amount_untaxed = fields.Float(string='Amount untaxed')

    invoice_number = fields.Char(string='Invoice number')
    amount_vat_ret = fields.Float(string='Amount tax')
    retention_amount = fields.Float(string='Retention', readonly=True, store=True)
    retention_rate = fields.Float(string='Rate', help="The retention rate can vary between 75% al 100% depending on the taxpayer.")
    
    move_id = fields.Many2one('account.move', string='Asiento')
    invoice_id = fields.Many2one('account.move', string='Invoice', ondelete='restrict', help="Retention invoice")

    tax_line_ids = fields.One2many('vat.retention.tax.lines', 'vat_ret_line_id', string='tax lines')
    #campo por agregar
    # tax_book_id = fields.Many2one('tax.book', string="Tax book")

    # campos a ser eliminados
    tax_id = fields.Many2one('account.tax', string='Tax')

    # sql constrain por agregar
    # _sql_constraints = [
    #     ('one_name', 'unique (invoice_id)', 'message')
    # ]




class RetentionVat(models.Model):
    """This is a main model for rentetion vat control."""
    _name = 'vat.retention'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    journal_id=fields.Char(string='journal_id')


    #@api.depends('retention_line_ids.retention_amount')
    def _amount_all(self):
        """ It shows total in this form view"""
        return 0
        #amount = 0
        #retention = 0
        #for invoice in self.retention_line_ids:
        #   amount += invoice.amount_untaxed
        #   retention += invoice.retention_amount
        #self.amount_untaxed = amount
        #self.vat_retentioned = retention

    @api.model
    def _type(self):
        """Return invoice type."""
        
        return self._context.get('type', 'in_invoice')

    
    # CORRELATIVO Segun indicaciones del seniat
    name = fields.Char(string='Voucher number', default='New')
    # datos del proveedor
    partner_id = fields.Many2one('res.partner', string='Partner', store=True)
    rif = fields.Char(string='RIF', store=True)
    # datos de emision y entrega del comprobante
    accouting_date = fields.Date(string='Accounting date', help='Voucher generation date', readonly="True")
    voucher_delivery_date = fields.Date(string='Voucher delivery date')
    # datos de la factura
    invoice_id = fields.Many2one('account.move', string="Invoice")
    invoice_number = fields.Char(string='Invoice Number')
    invoice_ctrl_num = fields.Char(string='Invoice control number')

    company_id = fields.Many2one('res.company', string="Company")

    # retenciones aplicadas
    retention_line_ids = fields.One2many('vat.retention.invoice.line', 'retention_id', string='Retention')
    
    # totales
    amount_untaxed = fields.Float(string='Amount untaxed', help='This concept is tax base')
    vat_retentioned = fields.Float(string='VAT retentioned')

    #datos contables
    # journal_id = fields.Many2one('account.journal', string='Journal')
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_id = fields.Many2one('account.account', string='Account')
    
    line_ids = fields.One2many('account.move.line', 'retention_id', string='Invoice lines',
        copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    
    type = fields.Selection(selection=[
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice','Supplier Invoince'),
        ], string="Type invoice", store=True, default=_type)

    # otra informacion
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            # ('done', 'Done'),
            ('cancel', 'Cancelled')
        ], string='Status', readonly=True, copy=False, tracking=True,
        default='draft')

    is_supplier = fields.Boolean(string='Supplier')
    is_customer = fields.Boolean(string='Customer')
    description = fields.Char(string="Description", help="Description about this voucher.")

    # variant va hacer eliminado
    variant = fields.Selection([
        ('invoice_vendors','Invoice vendors'),
    ], string='Type')
    

    @api.onchange('invoice_id')
    def _get_company(self):
        if self.invoice_id:
            self.company_id = self.invoice_id.company_id.id


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_posted(self):
        if not self.voucher_delivery_date:
            raise ValidationError("Debe establecer una fecha de entrega")
        self.state = 'posted'
        

    def action_draft(self):
        #self.state = 'draft'
        for item in self:
            _logger.info("\n\n\n\n self %s \n\n\n\n", type(self))
            _logger.info("\n\n\n self %s \n\n\n", self)

    
    def get_address(self, address):
        _logger.info("\n\n\n address %s \n\n\n", address.street)
        _logger.info("\n\n\n address %s \n\n\n", type(address.street))

        address = (str(address.street or '') + 
            str(address.street2 or '') +
            str(address.city or ' ') +
            str(address.state_id.name or ' ') +
            str(address.country_id.name or '') )
        return address

   
    def unlink(self):
        """Throw an exception if the retention voucher is not in cancel state."""
        for voucher in self:
            raise ValidationError(_("No se pueden eliminar comprobantes"))



    @api.model
    def create(self, vals):
        partners=vals['partners']
        del vals['partners']
        #raise UserError(_(' partners: %s')%partners)

        """    partners='pro' # aqui si es un proveedor
        if self.partner_id.customer_rank!=0:
            partners='cli'
        raise UserError(_(' partners: %s')%partners)"""

        if vals.get('name', 'New') == 'New':
            _logger.info("\n\n\n vals.get.tpye %s \n\n\n", vals.get('type', 'in_invoice'))

            if vals.get('type', 'in_invoice') == 'in_invoice':
                if partners!='cli':
                    vals['name'] = self.env['ir.sequence'].next_by_code('purchase.vat.retention.voucher.number') or '/'
                    _logger.info("\n\n\n vals[name] %s \n\n\n",vals['name'])
                else:
                    vals['name']= '00000000'
            else:
                vals['name'] = '/'
        return super().create(vals)


    