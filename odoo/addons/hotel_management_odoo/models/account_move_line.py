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

from odoo import fields, models


class AccountMoveLine(models.Model):
    """Adding fields to Account Move Line model."""
    _inherit = "account.move.line"

    product_type = fields.Selection([
        ('room', 'Room'),
        ('food', 'Food'),
        ('event', 'Event'),
        ('service', 'Service'),
        ('fleet', 'Fleet')],
        string="Product Type",
        help="Choose the product type")

    need_vehicle = fields.Boolean(
        string="Need Vehicle",
        help="Tick if this move line requires a vehicle"
    )

    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Vehicle",
        help="Vehicle related to this accounting line"
    )