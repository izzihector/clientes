# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions
import logging
from odoo.exceptions import UserError


class AccountBankSatatement(models.Model):
	_inherit = "account.bank.statement.line"
	validador = fields.Boolean(value=False)



class AccountBankStatementLine(models.Model):

	_inherit = "account.move"
	_decription = "Filtra las facturas que no aparescan en los libros"

	ocultar_libros = fields.Boolean(defaul=False, value=False)


class libro_compras(models.TransientModel):
    _inherit = "account.wizard.libro.compras"

    def get_invoice(self):
        self.facturas_ids = self.env['account.move'].search([
            ('invoice_date','>=',self.date_from),
            ('invoice_date','<=',self.date_to),
            ('ocultar_libros','!=','True'),
            ('state','in',('posted','cancel' )),
            ('type','in',('in_invoice','in_refund','in_receipt'))
            ],order="invoice_date asc")
        temp = self.env['account.wizard.pdf.compras'].search([])

        for t in temp:
            t.unlink()

        for factura in self.facturas_ids :
            for line in factura.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.aliquot:
                        self.env['account.wizard.pdf.compras'].create({
                            'name':factura.invoice_date,
                            'document': factura.partner_id.vat,
                            'partner':factura.partner_id.id,
                            'invoice_number': factura.invoice_number,#darrell
                            'tipo_doc': factura.journal_id.tipo_doc,
                            'invoice_ctrl_number': factura.invoice_ctrl_number,
                            'sale_total': line.price_total,
                            'base_imponible': line.price_subtotal,
                            'iva' : line.price_subtotal * (tax.amount / 100),
                            'state_retantion': factura.vat_ret_id.state,
                            'iva_retenido': factura.vat_ret_id.vat_retentioned,
                            'retenido': factura.vat_ret_id.name,
                            'retenido_date':factura.vat_ret_id.voucher_delivery_date,
                            'alicuota':tax.description,
                            'alicuota_type': tax.aliquot,
                            'state': factura.state,
                            'reversed_entry_id':factura.id,
                            'import_form_num':factura.import_form_num,
                            'import_dossier':factura.import_dossier,
                            'import_date': factura.import_date,
                            'ref':factura.ref,
                        })
        self.line = self.env['account.wizard.pdf.compras'].search([],order="name desc")
        pass

class libro_ventas(models.TransientModel):
    _inherit = "account.wizard.libro.ventas"

    def get_invoice(self):
        self.facturas_ids = self.env['account.move'].search([
            ('invoice_date','>=',self.date_from),
            ('invoice_date','<=',self.date_to),
            ('ocultar_libros','!=','True'),
            ('state','in',('posted','cancel' )),
            ('type','in',('out_invoice','out_refund','out_receipt'))
            ])
        temp = self.env['account.wizard.pdf.ventas'].search([])

        for t in temp:
            t.unlink()
        for factura in self.facturas_ids :
            for line in factura.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.aliquot:
                        self.env['account.wizard.pdf.ventas'].create({
                            'name':factura.invoice_date,
                            'document': factura.partner_id.vat,
                            'partner':factura.partner_id.id,
                            'invoice_number': factura.invoice_number,#darrell
                            'tipo_doc': factura.journal_id.tipo_doc,
                            'invoice_ctrl_number': factura.invoice_ctrl_number,
                            'sale_total': line.price_total,
                            'base_imponible': line.price_subtotal,
                            'iva' : line.price_subtotal * (tax.amount / 100),
                            'iva_retenido': factura.vat_ret_id.vat_retentioned,
                            'retenido': factura.vat_ret_id.name,
                            'state_retantion': factura.vat_ret_id.state,
                            'retenido_date':factura.vat_ret_id.voucher_delivery_date,
                            'alicuota':tax.description,
                            'alicuota_type': tax.aliquot,
                            'state': factura.state,
                            'reversed_entry_id':factura.reversed_entry_id.id,
                            'currency_id':factura.currency_id.id,
                            'ref':factura.ref,
                        })
        self.line = self.env['account.wizard.pdf.ventas'].search([])