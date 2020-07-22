# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _ 
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger('__name__')




class AccountMoveLine(models.Model):
    _inherit = "account.move.line"



    concept_id = fields.Many2one('muni.wh.concept', string='Municipal Tax')


    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]





class AccountMove(models.Model):
    _inherit = 'account.move'


    wh_muni_id = fields.Many2one('municipality.tax', string='Withholding municipal tax', readonly=True, copy=False)


    def _create_muni_wh_voucher(self):

        vals = {}
        values = {}
        muni_wh = self.env['municipality.tax']
        muni_wh_line = self.env['account.move.line']
        _logger.info("""\n\n\n Hola se esta ejecutando el action_post de la retencion municipal\n\n\n""")
        # _logger.info("""\n\n\n\n  invoice %s \n\n\n""", invoice)
        # se crea el registro del modelo municipality.tax.line
        res = []
        for item in self.invoice_line_ids:
            # codigo darrell
            base_impuesto=item.price_subtotal
            impuesto_mun=item.concept_id.aliquot
            # fin codigo darrell
            #raise UserError(_('impuesto_mun= %s')%impuesto_mun)
            if item.concept_id.aliquot>0:
                res.append((0,0, {
                    'code': item.concept_id.code,
                    'aliquot': item.concept_id.aliquot,
                    'concept_id': item.concept_id.id,
                    #'base_tax': self.amount_untaxed,
                    'base_tax': base_impuesto, # correcion darrell
                    'invoice_id': self.id,
                    'invoice_date' : self.date,
                    'invoice_number': self.invoice_number,
                    'invoice_ctrl_number': self.invoice_ctrl_number,
                    #'type':self.type,  # nuevo darrell
                }))
        _logger.info("\n\n\n res %s \n\n\n\n", res)
        # Se crea el registro de la retencion
        vals = {
           'partner_id': self.partner_id.id,
           'rif': self.partner_id.vat,
           'invoice_id': self.id,
           'act_code_ids': res,
           #'type':self.type,
        }
        _logger.info("\n\n\n vals %s \n\n\n", vals)
        muni_tax = muni_wh.create(vals)
        _logger.info("\n\n\n muni %s\n\n\n", muni_tax)
        self.write({'wh_muni_id': muni_tax.id})
        #raise UserError(_('cuentas = %s')%self.write({'wh_muni_id': muni_tax.id}))

    def actualiza_voucher_wh(self):
        #raise UserError(_('mama = %s')%self)
        cursor_municipality = self.env['municipality.tax'].search([('id','=',self.wh_muni_id.id)])
        for det in cursor_municipality:
            self.env['municipality.tax'].browse(det.id).write({
                'type': self.type,
                })


    def action_post(self):
        """This function create municital retention voucher too."""
        invoice = super().action_post()
        # es agente de retencion municipal
        _logger.info("\n\n\n\n action_post de Impuestos municipales \n\n\n\n")
      
        if self.partner_id.muni_wh_agent==True or self.company_id.partner_id.muni_wh_agent==True:
            # si no existe una retencion ya
            bann=0
            bann=self.verifica_exento_muni()
            if bann>0:
                if not self.wh_muni_id:
                    self._create_muni_wh_voucher()
                self.actualiza_voucher_wh()
        return invoice

    def verifica_exento_muni(self):
        acum=0
        #raise UserError(_('self = %s')%self.id)
        puntero_move_line = self.env['account.move.line'].search([('move_id','=',self.id)])
        for det_puntero in puntero_move_line:
            acum=acum+det_puntero.concept_id.aliquot
        return acum





