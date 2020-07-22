# -*- coding: utf-8 -*-


from odoo import api, fields, models, _




class Partners(models.Model):
    _inherit = 'res.partner'

    firma = fields.Binary(string='Firma digitalizada', help='Firma Digitalizada para comprobantes de retencion IVA, Municipal e ISLR')