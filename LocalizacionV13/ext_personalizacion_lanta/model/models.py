# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api, exceptions, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger('__name__')


class AccountInherit(models.Model):
    """This model add fields need in the invoice for accounting in Venezuela."""
    _inherit = 'account.move'

    #rif = fields.Char(related='partner_id.vat', string='RIF', store=True)
    """rif = fields.Char(compute='_concatena', string='RIF')

    @api.depends('partner_id')
    def _concatena(self):
        if self.partner_id.doc_type=="v":
            tipo_doc="V"
        if self.partner_id.doc_type=="e":
            self.partner_id.doc_type="E"
        if self.partner_id.doc_type=="g":
            tipo_doc="G"
        if self.partner_id.doc_type=="j":
            tipo_doc="J"
        if self.partner_id.doc_type=="p":
            tipo_doc="P"
        if self.partner_id.doc_type=="c":
            tipo_doc="C"
        if not self.partner_id.doc_type:
            tipo_doc="?"
        self.rif=str(tipo_doc)+"-"+str(self.partner_id.vat)"""

    def funcion_numeracion_fac(self):
        if self.type=="in_invoice":
            busca_correlativos = self.env['account.move'].search([('invoice_number','=',self.invoice_number_pro),('id','!=',self.id)])
            for det_corr in busca_correlativos:
                if det_corr.invoice_number:
                    raise UserError(_(' El valor :%s ya se uso en otro documento')%det_corr.invoice_number)

            busca_correlativos2 = self.env['account.move'].search([('invoice_ctrl_number','=',self.invoice_ctrl_number_pro),('id','!=',self.id)])
            for det_corr2 in busca_correlativos2:
                if det_corr2.invoice_ctrl_number:
                    raise UserError(_(' El nro de control :%s ya se uso en otro documento')%det_corr2.invoice_ctrl_number)
            
            self.invoice_number=self.invoice_number_pro
            self.invoice_ctrl_number=self.invoice_ctrl_number_pro
            partners='pro' # aqui si es un proveedor

        if self.type=="in_refund" or self.type=="in_receipt":
            busca_correlativos = self.env['account.move'].search([('invoice_number','=',self.refuld_number_pro),('id','!=',self.id)])
            for det_corr in busca_correlativos:
                if det_corr.invoice_number:
                    raise UserError(_(' El valor :%s ya se uso en otro documento')%det_corr.invoice_number)

            busca_correlativos2 = self.env['account.move'].search([('invoice_ctrl_number','=',self.refund_ctrl_number_pro),('id','!=',self.id)])
            for det_corr2 in busca_correlativos2:
                if det_corr2.invoice_ctrl_number:
                    raise UserError(_(' El nro de control :%s ya se uso en otro documento')%det_corr2.invoice_ctrl_number)
                    
            self.invoice_number=self.refuld_number_pro
            self.invoice_ctrl_number=self.refund_ctrl_number_pro
            partners='cli' # aqui si es un cliente

        if self.type=="out_invoice":
            self.invoice_number_cli=self.get_invoice_number_cli()
            self.invoice_number=self.invoice_number_cli #self.get_invoice_number_cli()
            self.invoice_ctrl_number_cli=self.get_invoice_ctrl_number_unico()
            self.invoice_ctrl_number=self.invoice_ctrl_number_cli #self.get_invoice_ctrl_number_cli()

        if self.type=="out_refund":
            self.refuld_number_cli=self.get_refuld_number_cli()
            self.invoice_number=self.refuld_number_cli #self.get_refuld_number_cli()
            self.refund_ctrl_number_cli=self.get_invoice_ctrl_number_unico()
            self.invoice_ctrl_number=self.refund_ctrl_number_cli #self.get_refuld_ctrl_number_cli()

        if self.type=="out_receipt":
            self.refuld_number_cli=self.get_refuld_number_pro()
            self.invoice_number=self.refuld_number_cli #self.get_refuld_number_cli()
            self.refund_ctrl_number_cli=self.get_invoice_ctrl_number_unico()
            self.invoice_ctrl_number=self.refund_ctrl_number_cli #self.get_refuld_ctrl_number_cli()
            #self.invoice_number=self.get_nro_cliente()

    def get_invoice_ctrl_number_unico(self):
        '''metodo que crea el Nombre del asiento contable si la secuencia no esta creada, crea una con el
        nombre: 'l10n_ve_cuenta_retencion_iva'''

        self.ensure_one()
        SEQUENCE_CODE = 'l10n_ve_nro_control_unico_formato_libre'
        company_id = 1
        IrSequence = self.env['ir.sequence'].with_context(force_company=1)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        # si aún no existe una secuencia para esta empresa, cree una
        if not name:
            IrSequence.sudo().create({
                'prefix': '00-',
                'name': 'Localización Venezolana nro control Unico Factura Forma Libre %s' % 1,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 4,
                'number_increment': 1,
                'company_id': 1,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        #self.invoice_number_cli=name
        return name