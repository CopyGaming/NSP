# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADARSH K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, tools

class ServiceBookingLine(models.Model):
    """Model that handles the service booking form"""
    _name = "service.booking.line"
    _description = "Hotel Service Line"

    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 ondelete="cascade", help="Room Booking reference")
    
    service_id = fields.Many2one('hotel.service', string="Service",
                                 help="Service selected")

    description = fields.Char(
        string='Description',
        related='service_id.name',
        store=True,  # WAJIB agar kolomnya ada di database
        help="Description of the Service"
    )

    uom_qty = fields.Float(string="Qty", default=1.0, help="Quantity")
    
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure",
                             default=_get_default_uom_id,
                             readonly=True)

    price_unit = fields.Float(string='Price',
                              related='service_id.unit_price',
                              digits='Product Price',
                              store=True)

    tax_ids = fields.Many2many('account.tax',
                               'hotel_service_order_line_taxes_rel',
                               'service_id', 'tax_id',
                               related='service_id.taxes_ids',
                               domain=[('type_tax_use', '=', 'sale')],
                               string='Taxes')

    currency_id = fields.Many2one('res.currency',
                                  related='booking_id.pricelist_id.currency_id',
                                  store=True)

    price_subtotal = fields.Monetary(string="Subtotal",
                                     compute='_compute_price_subtotal',
                                     store=True,
                                     currency_field='currency_id')

    price_tax = fields.Monetary(string="Total Tax",
                                compute='_compute_price_subtotal',
                                store=True,
                                currency_field='currency_id')

    price_total = fields.Monetary(string="Total",
                                  compute='_compute_price_subtotal',
                                  store=True,
                                  currency_field='currency_id')

    state = fields.Selection(related='booking_id.state',
                             string="Booking Status",
                             copy=False)

    booking_line_visible = fields.Boolean(default=False,
                                          string="Booking Line Visible")

    @api.depends('uom_qty', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_price_subtotal(self):
        """Compute the amounts of the service booking line."""
        for line in self:
            # Default value
            line.price_subtotal = 0.0
            line.price_tax = 0.0
            line.price_total = 0.0

            if not line.currency_id or not line.price_unit:
                continue

            if line.tax_ids:
                # Perhitungan pakai account.tax
                base_line = line.env['account.tax']._prepare_base_line_for_taxes_computation(
                    line,
                    tax_ids=line.tax_ids,
                    price_unit=line.price_unit,
                    quantity=line.uom_qty,
                    currency_id=line.currency_id,
                    partner_id=line.booking_id.partner_id,
                    is_refund=False
                )

                line.env['account.tax']._add_tax_details_in_base_line(base_line, line.env.company)

                tax_details = base_line.get('tax_details', {})
                total_excluded = tax_details.get('total_excluded_currency') or tax_details.get('total_excluded') or 0.0
                total_included = tax_details.get('total_included_currency') or tax_details.get('total_included') or 0.0

                line.price_subtotal = total_excluded
                line.price_total = total_included
                line.price_tax = total_included - total_excluded
            else:
                # Perhitungan manual jika tidak ada pajak
                line.price_subtotal = line.uom_qty * line.price_unit
                line.price_total = line.price_subtotal
                line.price_tax = 0.0



    def _prepare_base_line_for_taxes_computation(self):
        """Convert record for tax computation."""
        self.ensure_one()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            tax_ids=self.tax_ids,
            price_unit=self.price_unit,
            quantity=self.uom_qty,
            currency_id=self.currency_id,
            partner_id=self.booking_id.partner_id,
            is_refund=False,
        )