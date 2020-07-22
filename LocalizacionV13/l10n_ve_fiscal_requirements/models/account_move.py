# -*- coding: utf-8 -*-

from odoo import api, fields, models, _ 



class AccountInherit(models.Model):
    """This model add fields need in the invoice for accounting in Venezuela."""
    _inherit = 'account.move'

    rif = fields.Char(related='partner_id.vat', string='RIF', store=True)
    invoice_number = fields.Char(string='Invoice number', required=False)
    invoice_ctrl_number = fields.Char(string='Invoice control number', required=False)
    import_form_num = fields.Char(string='Import form number')
    import_dossier = fields.Char(string='Import dossier number')



class AccountTax(models.Model):
    _inherit = 'account.tax'

    aliquot = fields.Selection(selection=[
        ('no_tax_credit','No tax Credit'),
        ('exempt','Exempt'),
        ('general','General Aliquiot'),
        ('reduced','Reducted Aliquot'),
        ('additional','General Aliquiot + Additiona'),
        ], string='Aliquot', help='Specifies which aliquot is processed depending on the purchase book or sales book.')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    type = fields.Selection(selection=[
        ('sale','Sale'),
        ('sale_refund','Sale refund'),
        ('purchase','Purchase'),
        ('purchase_refund','Purchase refund'),
        ('cash', 'Cash'),
        ('bank','Bank and Check'),
        ('general','General'),
        ('situation', 'Opening/Closing situation'),
        ('sale_debit', 'Sale Debit'),
        ('purchase_debit', 'Purchase Debit'),
    ], string='type')
    note = fields.Text(string='Note about field type')
