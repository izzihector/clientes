# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _ 


_logger = logging.getLogger('__name__')

class Partner(models.Model):
    _inherit = 'res.partner'


    vat = fields.Char(string='Tax ID', help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    vendor = fields.Selection([
        ('national','National'),
        ('international','International'),
    ])
    vat_retention_rate = fields.Float(string='Retention rate', 
        help='VAT retention rate according to the Seniat for this contributes', 
        required=True
    )
    vat_tax_account_id = fields.Many2one('account.tax', string='Impuesto de Retencion')
    people_type = fields.Selection(string='People type', selection=[
        ('resident_nat_people','PNRE Residente Natural Person'),
        ('non_resit_nat_people','PNNR Non-resident Natural Person'),
        ('domi_ledal_entity','PJDO Domiciled Legal Entity'),
        ('legal_ent_not_domicilied','PJDO Legal Entity Not Domiciled'),
    ], required="True")
    seniat_url = fields.Char(string='GO SENIAT',readonly="True", default="http://contribuyente.seniat.gob.ve/BuscaRif/BuscaRif.jsp")


    @api.onchange('vat','vendor')
    def _clean_vat(self):
        if self.vendor == 'international':
            self.vat = ''
                
