# # -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
import logging

import io
from io import BytesIO
from io import StringIO

import xlsxwriter
import shutil
import base64
import csv

import urllib.request

import requests

_logger = logging.getLogger(__name__)

def rif_format(valor):
    if valor:
        return valor.replace('-','')
    return '0'

def tipo_format(valor):
    if valor and valor=='in_refund':
        return '03'
    return '01'

def float_format(valor):
    if valor:
        result = '{:,.2f}'.format(valor)
        #_logger.info('Result 1: %s' % result)
        result = result.replace(',','')
        #_logger.info('Result 2: %s' % result)
        return result
    return valor

class BsoftContratoReport2(models.TransientModel):
    _name = 'snc.wizard.retencioniva'
    _description = 'Generar archivo TXT de retenciones de IVA'

    delimiter = '\t'
    quotechar = "'"
    date_from = fields.Date(string='Fecha de Llegada', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Fecha de Salida', default=lambda *a:(datetime.now() + timedelta(days=(1))).strftime('%Y-%m-%d'))
    file_data = fields.Binary('Archivo TXT', filters=None, help="")
    file_name = fields.Char('txt_generacion.txt', size=256, required=False, help="",)

    def show_view(self, name, model, id_xml, res_id=None, view_mode='tree,form', nodestroy=True, target='new'):
        context = self._context
        mod_obj = self.env['ir.model.data']
        view_obj = self.env['ir.ui.view']
        module = ""
        view_id = self.env.ref(id_xml).id
        if view_id:
            view = view_obj.browse(view_id)
            view_mode = view.type
        ctx = context.copy()
        ctx.update({'active_model': model})
        res = {'name': name,
                'view_type': 'form',
                'view_mode': view_mode,
                'view_id': view_id,
                'res_model': model,
                'res_id': res_id,
                'nodestroy': nodestroy,
                'target': target,
                'type': 'ir.actions.act_window',
                'context': ctx,
                }
        return res

    def action_generate_txt(self):

        #dominio = (('id','=',True),('invoice_id.type','in',('in_invoice', 'in_refund')),('invoice_id.amount_tax','!=',0.00))

        #if self.date_from:
        #    dominio.append(('create_date','>=',self.date_from))

        #if self.date_to:
        #    dominio.append(('create_date','<=',self.date_to))

        #rec_ids = self.env['account.move'].search(dominio).ids
        rec_cursor = self.env['account.move'].search([('date','>=',self.date_from),('date','<=',self.date_to),('type','=','out_invoice'),('state','=','posted')])
        #_logger.info("\n\n\n {} \n\n\n".format(self.rec_cursor))

        self.file_name = 'txt_generacion.txt'

        #ruta="C:/Odoo 13.0e/server/odoo/LocalizacionV13/vat_retention/wizard/txt_generacion.txt"
        ruta="/opt/odoo/addons/vat_retention/wizard/txt_generacion.txt"


        with open(ruta, "w") as file:

            for rec in rec_cursor:
                periodo = '%s'%(rec.invoice_date)
                periodo = periodo.replace('-','')
                periodo = periodo[0:0]
                exento = abs(rec.amount_total-rec.amount_untaxed+rec.amount_tax+rec.amount_total)
                total = rec.amount_total
                por_iva = rec.amount_tax/rec.amount_total*100
                fecha = rec.invoice_date
                su_rif= rif_format(rec.partner_id.vat)
                rif_2 = rif_format(rec.company_id.vat)
                refer = rec.ref
                total2 = str(total)
                base_imponible = str(rec.amount_untaxed)
                amount = str(rec.amount_total)

                refer = str(refer)
                number_retiva = str(rec.invoice_number)
                exento = str(exento)
                por_iva = str(por_iva)
                fecha = str(fecha)
                invoice_sequence = str(rec.invoice_ctrl_number)

                file.write(su_rif)
                file.write(periodo + "\t")
                file.write(fecha + "\t")

                file.write("C" + "\t")
                file.write("01" + "\t")
                file.write(rif_2 + "\t")


                file.write(rec.name + "\t")
                file.write(invoice_sequence + "\t")
                file.write(total2 + "\t")

                file.write(base_imponible + "\t")
                file.write(amount + "\t")
                file.write(refer + "\t")

                file.write(number_retiva + "\t")
                file.write(exento + "\t")
                file.write("16" + "\t")

                file.write('0' + "\n")





        self.write({'file_data': base64.encodestring(open(ruta, "rb").read()),
                    'file_name': "Retenciones de IVA desde %s hasta %s.txt"%(self.date_from,self.date_to),
                    })

        return self.show_view('Archivo Generado', self._name, 'vat_retention.snc_wizard_retencioniva_form_view', self.id)
