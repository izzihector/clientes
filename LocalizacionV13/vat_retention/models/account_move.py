# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


_logger = logging.getLogger('__name__')

class AccountMove(models.Model):
    _inherit = 'account.move'

    

    vat_ret_id = fields.Many2one('vat.retention', string='VAT withheld', readonly="True", copy=False, help='VAT retention voucher')


    # Main Function
    def action_post(self):
        super().action_post()
        # Acciones a realizar validar fechas contables en la factura
        # Verificar si existe el impuesto al iva (lo voy a crear y cargar en xml)
        # Verificar si la empresa como el cliente o proveedor son agentes de retencion
        
        # si es agente de retencion
        if self.partner_id.ret_agent:
            _logger.info("\n\n\n\n Si es agente de retention\n\n\n\n", self.partner_id.ret_agent)
            self.action_create_vat_retention()
            id_vat_ret=self.vat_ret_id.id  
            #raise UserError(_(' id retencion:%s')%id_vat_ret)          
            self.actualiza_voucher(id_vat_ret) #self.asiento_retencion(self.id,id_vat_ret) #funtcion darrell
            #self.actualiza_voucher(id_vat_ret)
        
        
    def action_create_vat_retention(self):
        "This function created the VAT retention Voucher"

        # si existe una retencion lo logico es que no agregue otra
        if self.vat_ret_id:
            if self.vat_ret_id.state == 'draft':
                pass
            #else:
            #    raise ValidatioError('The invoice already has an associated VAT retention')
        
        else:
            # Aqui puede ir tu funcion Darrel
            self.create_voucher()
            # se crean los asientos
            #self.asiento_retencion(self.id)

    
    def create_voucher(self):
        if self.partner_id.supplier_rank!=0:
            partners='pro' # aqui si es un proveedor
        if self.partner_id.customer_rank!=0:
            partners='cli' # aqui si es un cliente
        """Esta funcion crea el comprobante de retencion."""
        #res = []
        #taxes = self.invoice_line_ids.tax_ids
        #base_imponible = self.amount_untaxed
        #_logger.info("\n\n\n taxes %s \n\n\n",taxes.ids)
        #_logger.info("\n\n\n base_imponible %s \n\n\n",base_imponible)
        #for tax in taxes:
        #    res.append((0,0, {
        #        'move_id': self.id,
        #        'invoice_number': self.invoice_number,
        #        
        #    }))

        # SE BUSCA CREAR EL DETALLE DE LA RETENCION
        # details_ret = self.env['vat.retention.tax.lines']
        # det = {
        #     'name': 'Retención de IVA',
        #     'base_tax': self.amount_untaxed,
        #     'tax_amount': self.,
        # }




        # SE BUSCA CREAR LA LINEA DE RETENCION
        ret_lines = self.env['vat.retention.invoice.line']
        values = {
            'name': self.name,
            'invoice_id': self.id,
            'invoice_number': self.invoice_number,
            'amount_untaxed': self.amount_untaxed,
            'retention_rate': self.partner_id.vat_retention_rate,
        }
        _logger.info("\n\n\n values %s\n\n\n", values)
        #retention_id = ret_lines.create(values)
        #_logger.info('\n\n\n\n retention_id %s\n\n\n', retention_id)
        
        # SE CREA LA RETENTION
        retention = self.env['vat.retention']
        _logger.info("\n\n\n retention %s\n\n\n", retention)
        vals = {
            'rif': self.rif,
            'partner_id': self.partner_id.id,
            'accouting_date': datetime.now(),
            'invoice_number': self.invoice_number,
            'invoice_id': self.id,
            'amount_untaxed': self.amount_untaxed,
            'retention_line_ids':  [(0, 0, values)],
            'partners':partners,
        }
        ret = retention.create(vals)
        _logger.info("\n\n\n ret %s\n\n\n", ret)
        self.write({'vat_ret_id':ret.id})
        return ret #devuelve el ide de la retencion
        #ret_lines.write({'retention_id':ret.id})

    def actualiza_voucher(self,ret_id):
        
        id_factura=self.id # USAR
        retencion=69
        #imponible_base=self.amount_untaxed
        #raise UserError(_('imponible_base = %s')%imponible_base)
        impuesto_ret_id=self.partner_id.vat_tax_account_id.id # USAR
        agente_ret=self.partner_id.ret_agent # USAR AQUI INDICA SI ES O NO AGENTE DE RETENCION
        porcentaje_ret=self.partner_id.vat_retention_rate #usar para meterlo en la tabla vat.retention
        cuenta_ret_cobrar=self.partner_id.account_ret_receivable_id.id # USAR PARA COMPARAR CON EL CAMPO ACCOUNT_ID DE LA TABLA ACCOUNT_MOVE_LINE
        cuenta_ret_pagar = self.partner_id.account_ret_payable_id.id # USAR PARA COMPARAR CON EL CAMPO ACCOUNT_ID DE LA TABLA ACCOUNT_MOVE_LINE
        cuenta_clien_cobrar=self.partner_id.property_account_receivable_id.id
        cuenta_prove_pagar = self.partner_id.property_account_payable_id.id
        #raise UserError(_('id_factura = %s')%id_factura) 
        valor_iva=self.amount_tax # ya este valo ya no me sirve segun la nueva metodologia
        valor_ret=round(float(valor_iva*porcentaje_ret/100),2)
        valores=valor_ret
        #raise UserError(_('valor_iva = %s')%valor_iva) 
        if self.partner_id.supplier_rank!=0:
            partnerr='pro' # aqui si es un proveedor
            id_account=cuenta_ret_pagar
        if self.partner_id.customer_rank!=0:
            partnerr='cli' # aqui si es un cliente
            id_account=cuenta_ret_cobrar
        #raise UserError(_('id_factura = %s')%id_factura)
        line_moves = self.env['account.move.line'].search([('move_id','=',id_factura),('account_id','=',id_account)])
        for det_line_move in line_moves:
            retencion=det_line_move.price_unit
        retencion=abs(retencion)

        imponible_base=valor_iva+retencion
        lista_account_retention_line = self.env['vat.retention.invoice.line'].search([('retention_id','=',ret_id)])
        #raise UserError(_('lista_account_retention_line = %s')%lista_account_retention_line)
        for det_line_retention in lista_account_retention_line:
            self.env['vat.retention.invoice.line'].browse(det_line_retention.id).write({
                'retention_amount': retencion,
                'retention_rate':porcentaje_ret,
                'move_id':id_factura,
                'amount_vat_ret':imponible_base,
                })
        lista_account_retention = self.env['vat.retention'].search([('id','=',ret_id)])
        for det_retention in lista_account_retention:
            self.env['vat.retention'].browse(det_retention.id).write({
                'vat_retentioned': retencion,
                'journal_id':self.journal_id.id,
                'amount_untaxed':imponible_base,
                })
        # CODIGO QUE VALIDA SI EN LA FACTURA SE LE APLICA EL IMPUESTO DE RETENCION DEL PROVEEDOR QUE ESTA CONFIGURADO    
        valida_mov_lin=self.env['account.move.line'].search([('move_id','=',id_factura),('tax_line_id','=',impuesto_ret_id)])
        if valida_mov_lin.tax_line_id.id== False:
            raise UserError(_('Este Persona / Empresa debe aplicarse el impuesto de retencion :( %s)')%self.partner_id.vat_tax_account_id.name) 


        #moves= self.env['account.move'].search([('id','=',id_factura)])
        #moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()  