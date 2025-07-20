# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADARSH K (odoo@cybrosys.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

###############################################################################

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class RoomBookingLine(models.Model):
    _name = "room.booking.line"
    _description = "Hotel Folio Line"
    _rec_name = 'room_id'

    @tools.ormcache()
    def _set_default_uom_id(self):
        """Set default UoM to 'Day' with rounding > 0. If not valid, fallback to UoM 'Unit'."""
        uom_day = self.env.ref('uom.product_uom_day', raise_if_not_found=False)
        if uom_day and uom_day.rounding and uom_day.rounding > 0.0:
            return uom_day.id
        else:
            uom_unit = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            if uom_unit and uom_unit.rounding and uom_unit.rounding > 0.0:
                return uom_unit.id
            raise ValidationError(
                _("No valid Unit of Measure found with positive rounding. Please check your UoM configuration."))

    booking_id = fields.Many2one("room.booking", string="Booking", ondelete="cascade")
    checkin_date = fields.Datetime(string="Check In", required=True)
    checkout_date = fields.Datetime(string="Check Out", required=True)

    room_id = fields.Many2one('hotel.room', string="Room", required=True)

    room_type = fields.Selection([
        ('redDoorz Room', 'RedDoorz Room'),
        ('redDoorz Deluxe Twin Room', 'RedDoorz Deluxe Twin Room'),
        ('redDoorz Deluxe Room', 'RedDoorz Deluxe Room'),
        ('family Room', 'Family Room')],
        string="Room Type")



    uom_qty = fields.Float(string="Duration", readonly=True)
    uom_id = fields.Many2one('uom.uom', default=_set_default_uom_id, string="Unit of Measure", readonly=True)

    price_unit = fields.Float(string='Rent')
    tax_ids = fields.Many2many('account.tax', 'hotel_room_order_line_taxes_rel', 'room_id', 'tax_id',
                               string='Taxes', domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(string='Currency', related='booking_id.pricelist_id.currency_id')

    price_subtotal = fields.Float(string="Subtotal", compute='_compute_price_subtotal', store=True)
    price_tax = fields.Float(string="Total Tax", compute='_compute_price_subtotal', store=True)
    price_total = fields.Float(string="Total", compute='_compute_price_subtotal', store=True)

    state = fields.Selection(related='booking_id.state', string="Order Status", copy=False)
    booking_line_visible = fields.Boolean(default=False, string="Booking Line Visible")

    @api.onchange('room_id')
    def _onchange_room_id(self):
        self.room_type = self.room_id.room_type  # tanpa .id karena ini Selection
        self._onchange_room_type()

    @api.onchange('room_type')
    def _onchange_room_type(self):

        # Tidak lakukan apa pun, biarkan user isi manual
        pass

    @api.constrains('price_unit', 'room_type')
    def _check_price_unit_required(self):
        for rec in self:
            if rec.room_type and (rec.price_unit is None or rec.price_unit <= 0.0):
                raise ValidationError(
                    _("Harga sewa (Rent) wajib diisi."))

        if self.room_type == 'single':
            self.price_unit = 45000000
        elif self.room_type == 'double':
            self.price_unit = 90000000
        elif self.room_type == 'dormitory':
            self.price_unit = 110000000

        # Tambahan: update ke hotel.room
        if self.room_id:
            person_map = {'single': 1, 'double': 2, 'dormitory': 4}
            self.room_id.room_type = self.room_type
            self.room_id.num_person = person_map.get(self.room_type, 1)


    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):
        if self.checkout_date and self.checkin_date:
            if self.checkout_date < self.checkin_date:
                raise ValidationError("Checkout must be after check-in date.")
            diffdate = self.checkout_date - self.checkin_date
            qty = diffdate.days
            if diffdate.total_seconds() > 0:
                qty += 1
            self.uom_qty = qty

    @api.depends('uom_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()

            # Filter hanya tax yang valid dan bukan group
            base_line['tax_ids'] = base_line.get('tax_ids', self.env['account.tax']).filtered(
                lambda tax: tax.amount_type != 'group' and tax.rounding and tax.rounding > 0.0
            )

            if base_line['tax_ids']:
                self.env['account.tax']._add_tax_details_in_base_line(base_line, self.env.company)
                line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
                line.price_total = base_line['tax_details']['raw_total_included_currency']
                line.price_tax = line.price_total - line.price_subtotal
            else:
                line.price_subtotal = line.uom_qty * line.price_unit
                line.price_tax = 0.0
                line.price_total = line.price_subtotal

    def _prepare_base_line_for_taxes_computation(self):
        self.ensure_one()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            tax_ids=self.tax_ids,
            quantity=self.uom_qty,
            partner_id=self.booking_id.partner_id,
            currency_id=self.currency_id,
        )

    @api.onchange('checkin_date', 'checkout_date', 'room_id')
    def onchange_checkin_date_conflict(self):

        # Check room conflict

        bookings = self.env['room.booking'].search([('state', 'in', ['reserved', 'check_in'])])
        for booking in bookings:
            for rec_line in booking.room_line_ids:
                if rec_line.room_id == self.room_id and rec_line.id != self.id:
                    if (rec_line.checkin_date <= self.checkin_date <= rec_line.checkout_date or
                        rec_line.checkin_date <= self.checkout_date <= rec_line.checkout_date or
                        (self.checkin_date <= rec_line.checkin_date and self.checkout_date >= rec_line.checkout_date)):
                        raise ValidationError(_(
                            "This room is already booked for the selected dates. Please choose different dates or room."))
