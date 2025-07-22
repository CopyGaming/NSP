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
###############################################################################

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    """Model that holds all details regarding hotel room"""
    _name = 'hotel.room'
    _description = 'Rooms'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @tools.ormcache()
    def _get_default_uom_id(self):
        """Method for getting the default uom id"""
        return self.env.ref('uom.product_uom_unit')

    name = fields.Char(
        string='Name',
        help="Name of the Room",
        index='trigram',
        required=True,
        translate=True
    )

    status = fields.Selection([
        ("available", "Available"),
        ("reserved", "Reserved"),
        ("occupied", "Occupied")],
        default="available",
        string="Status",
        help="Status of The Room",
        tracking=True
    )

    is_room_avail = fields.Boolean(
        default=True,
        string="Available",
        help="Check if the room is available"
    )

    list_price = fields.Float(
        string='Rent',
        digits='Product Price',
        help="The rent of the room."
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        default=_get_default_uom_id,
        required=True,
        help="Default unit of measure used for all stock operations."
    )

    room_image = fields.Image(
        string="Room Image",
        max_width=1920,
        max_height=1920,
        help='Image of the room'
    )

    taxes_ids = fields.Many2many(
        'account.tax',
        'hotel_room_taxes_rel',
        'room_id', 'tax_id',
        help="Default taxes used when selling the room.",
        string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')],
        default=lambda self: self.env.company.account_sale_tax_id
    )

    room_amenities_ids = fields.Many2many(
        "hotel.amenity",
        string="Room Amenities",
        help="List of room amenities."
    )

    floor_id = fields.Many2one(
        'hotel.floor',
        string='Floor',
        help="Automatically selects the Floor",
        tracking=True
    )

    user_id = fields.Many2one(
        'res.users',
        string="User",
        related='floor_id.user_id',
        help="Automatically selects the manager",
        tracking=True
    )

    room_type = fields.Selection([
        ('redDoorz Room', 'RedDoorz Room'),
        ('redDoorz Deluxe Twin Room', 'RedDoorz Deluxe Twin Room'),
        ('redDoorz Deluxe Room', 'RedDoorz Deluxe Room'),
        ('family Room', 'Family Room')],
        required=True,
        string="Room Type",
        help="Automatically selects the Room Type",
        tracking=True,
        default="redDoorz Room"
    )

    num_person = fields.Integer(
        string='Number Of Persons',
        required=True,
        help="Automatically chooses the No. of Persons",
        tracking=True
    )

    description = fields.Html(
        string='Description',
        help="Add description",
        translate=True
    )

    clean_status = fields.Selection([
        ('clean', 'Clean'),
        ('dirty', 'Dirty')],
        string="Clean Status",
        default='clean',
        tracking=True
    )

    color_class = fields.Char(
        string='Color Class',
        compute='_compute_color_class',
        store=True
    )

    @api.constrains("num_person")
    def _check_capacity(self):
        for room in self:
            if room.num_person <= 0:
                raise ValidationError(_("Room capacity must be more than 0"))

    @api.onchange('room_type')
    def _onchange_room_type(self):
        # Tidak lakukan apa pun, biarkan user isi manual
        pass

    @api.depends('status', 'clean_status')
    def _compute_color_class(self):
        for room in self:
            if room.status == 'occupied':
                room.color_class = 'room-occupied'
            elif room.status == 'reserved':
                room.color_class = 'room-reserved'
            elif room.status == 'available' and room.clean_status == 'dirty':
                room.color_class = 'room-dirty'
            elif room.status == 'available' and room.clean_status == 'clean':
                room.color_class = 'room-clean'
            else:
                room.color_class = ''

    def action_mark_clean(self):
        """Mark room as clean from Room Chart"""
        for room in self:
            room.clean_status = 'clean'