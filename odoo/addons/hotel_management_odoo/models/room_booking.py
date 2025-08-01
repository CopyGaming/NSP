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
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import pytz


class RoomBooking(models.Model):
    """Model that handles the hotel room booking and all operations related
     to booking"""
    _name = "room.booking"
    _description = "Hotel Room Reservation"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Booking Reference', required=True, readonly=True, default='New')

    company_id = fields.Many2one('res.company', string="Company",
                                 help="Choose the Company",
                                 required=True, index=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Customers of hotel",
                                 required=True, index=True, tracking=1,
                                 domain="[('type', '!=', 'private'),"
                                        " ('company_id', 'in', "
                                        "(False, company_id))]")
    reserved_by_id = fields.Many2one('res.users', string='Reserved By')
    checkin_by_id = fields.Many2one('res.users', string='Check-In By')
    checkout_by_id = fields.Many2one('res.users', string='Check-Out By')
    team_id = fields.Many2one('crm.team', string='Sales Team')

    @api.onchange('state')
    def action_reserve(self):
        for rec in self:
            rec.reserved_by_id = self.env.user
            rec.state = 'reserved'

    def action_checkin(self):
        for rec in self:
            rec.checkin_by_id = self.env.user
            rec.state = 'check_in'

    def action_checkout(self):
        for rec in self:
            rec.checkout_by_id = self.env.user
            rec.state = 'check_out'

    date_order = fields.Datetime(string="Order Date",
                                 required=True, copy=False,
                                 help="Creation date of draft/sent orders,"
                                      " Confirmation date of confirmed orders",
                                 default=fields.Datetime.now)
    is_checkin = fields.Boolean(default=False, string="Is Checkin",
                                help="sets to True if the room is occupied")
    ktp_received = fields.Boolean(string='KTP Diterima', default=False)
    pic_ktp = fields.Binary(string='Foto KTP', attachment=True, default=False)

    @api.constrains('foto_ktp_file', 'ktp_received')
    def _check_pic_ktp(self):
        for rec in self:
            if rec.ktp_received and not rec.foto_ktp_file:
                raise ValidationError("Foto KTP wajib diunggah sebelum menyimpan data.")

    deposit_received = fields.Boolean(string='Deposit Diterima', default=False)

    maintenance_request_sent = fields.Boolean(default=False,
                                              string="Maintenance Request sent"
                                                     "or Not",
                                              help="sets to True if the "
                                                   "maintenance request send "
                                                   "once")
    checkin_date = fields.Datetime(string="Check In",
                                   help="Date of Checkin",
                                   default=fields.Datetime.now())
    checkout_date = fields.Datetime(string="Check Out",
                                    help="Date of Checkout",
                                    default=fields.Datetime.now() + timedelta(
                                        hours=23, minutes=59, seconds=59))
    hotel_policy = fields.Selection([("prepaid", "On Booking"),
                                     ("manual", "On Check In"),
                                     ("picking", "On Checkout"),
                                     ],
                                    default="manual", string="Hotel Policy",
                                    help="Hotel policy for payment that "
                                         "either the guest has to pay at "
                                         "booking time, check-in "
                                         "or check-out time.", tracking=True)
    duration = fields.Integer(string="Duration in Days",
                              help="Number of days which will automatically "
                                   "count from the check-in and check-out "
                                   "date.", )
    invoice_button_visible = fields.Boolean(string='Invoice Button Display', copy=False,
                                            help="Invoice button will be "
                                                 "visible if this button is "
                                                 "True")
    invoice_status = fields.Selection(
        selection=[('no_invoice', 'Nothing To Invoice'),
                   ('to_invoice', 'To Invoice'),
                   ('invoiced', 'Invoiced'),
                   ], string="Invoice Status",
        help="Status of the Invoice", copy=False,
        default='no_invoice', tracking=True)
    hotel_invoice_id = fields.Many2one("account.move",
                                       string="Invoice",
                                       help="Indicates the invoice",
                                       copy=False)
    duration_visible = fields.Float(string="Duration",
                                    help="A dummy field for Duration")
    need_service = fields.Boolean(default=False, string="Need Service",
                                  help="Check if a Service to be added with"
                                       " the Booking")
    need_fleet = fields.Boolean(default=False, string="Need Vehicle",
                                help="Check if a Fleet to be"
                                     " added with the Booking")
    need_food = fields.Boolean(default=False, string="Need Food",
                               help="Check if a Food to be added with"
                                    " the Booking")
    need_event = fields.Boolean(default=False, string="Need Event",
                                help="Check if a Event to be added with"
                                     " the Booking")
    service_line_ids = fields.One2many("service.booking.line",
                                       "booking_id",
                                       string="Service",
                                       help="Hotel services details provided to"
                                            "Customer and it will included in "
                                            "the main Invoice.")
    event_line_ids = fields.One2many("event.booking.line",
                                     'booking_id',
                                     string="Event",
                                     help="Hotel event reservation detail.")
    vehicle_line_ids = fields.One2many("fleet.booking.line",
                                       "booking_id",
                                       string="Vehicle",
                                       help="Hotel fleet reservation detail.")
    room_line_ids = fields.One2many("room.booking.line",
                                    "booking_id", string="Room",
                                    help="Hotel room reservation detail.")
    food_order_line_ids = fields.One2many("food.booking.line",
                                          "booking_id",
                                          string='Food',
                                          help="Food details provided"
                                               " to Customer and"
                                               " it will included in the "
                                               "main invoice.", )
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('reserved', 'Reserved'),
                                        ('check_in', 'Check In'),
                                        ('check_out', 'Check Out'),
                                        ('cancel', 'Cancelled'),
                                        ('done', 'Done')], string='State',
                             help="State of the Booking",
                             default='draft', tracking=True, copy=False, )
    user_id = fields.Many2one(comodel_name='res.partner',
                              string="Invoice Address",
                              compute='_compute_user_id',
                              help="Sets the User automatically",
                              required=True,
                              domain="['|', ('company_id', '=', False), "
                                     "('company_id', '=',"
                                     " company_id)]")
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',
                                   string="Pricelist",
                                   compute='_compute_pricelist_id',
                                   store=True, readonly=False,
                                   required=False,
                                   tracking=1,
                                   help="If you change the pricelist,"
                                        " only newly added lines"
                                        " will be affected.")
    currency_id = fields.Many2one(
        string="Currency", help="This is the Currency used",
        related='pricelist_id.currency_id',
        depends=['pricelist_id.currency_id'], )
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   string="Invoice "
                                          "Count",
                                   help="The number of invoices created")
    account_move = fields.Integer(string='Invoice Id',
                                  help="Id of the invoice created")
    amount_untaxed = fields.Monetary(string="Total Untaxed Amount",
                                     help="This indicates the total untaxed "
                                          "amount", store=True,
                                     compute='_compute_amount_untaxed',
                                     tracking=5)
    amount_tax = fields.Monetary(string="Taxes", help="Total Tax Amount",
                                 store=True, compute='_compute_amount_untaxed')
    amount_total = fields.Monetary(string="Total", store=True,
                                   help="The total Amount including Tax",
                                   compute='_compute_amount_untaxed',
                                   tracking=4)
    amount_untaxed_room = fields.Monetary(string="Room Untaxed",
                                          help="Untaxed Amount for Room",
                                          compute='_compute_amount_untaxed',
                                          tracking=5)
    amount_untaxed_food = fields.Monetary(string="Food Untaxed",
                                          help="Untaxed Amount for Food",
                                          compute='_compute_amount_untaxed',
                                          tracking=5)
    amount_untaxed_event = fields.Monetary(string="Event Untaxed",
                                           help="Untaxed Amount for Event",
                                           compute='_compute_amount_untaxed',
                                           tracking=5)
    amount_untaxed_service = fields.Monetary(
        string="Service Untaxed", help="Untaxed Amount for Service",
        compute='_compute_amount_untaxed', tracking=5)
    amount_untaxed_fleet = fields.Monetary(string="Amount Untaxed",
                                           help="Untaxed amount for Fleet",
                                           compute='_compute_amount_untaxed',
                                           tracking=5)
    amount_taxed_room = fields.Monetary(string="Rom Tax", help="Tax for Room",
                                        compute='_compute_amount_untaxed',
                                        tracking=5)
    amount_taxed_food = fields.Monetary(string="Food Tax", help="Tax for Food",
                                        compute='_compute_amount_untaxed',
                                        tracking=5)
    amount_taxed_event = fields.Monetary(string="Event Tax",
                                         help="Tax for Event",
                                         compute='_compute_amount_untaxed',
                                         tracking=5)
    amount_taxed_service = fields.Monetary(string="Service Tax",
                                           compute='_compute_amount_untaxed',
                                           help="Tax for Service", tracking=5)
    amount_taxed_fleet = fields.Monetary(string="Fleet Tax",
                                         compute='_compute_amount_untaxed',
                                         help="Tax for Fleet", tracking=5)
    amount_total_room = fields.Monetary(string="Total Amount for Room",
                                        compute='_compute_amount_untaxed',
                                        help="This is the Total Amount for "
                                             "Room", tracking=5)
    amount_total_food = fields.Monetary(string="Total Amount for Food",
                                        compute='_compute_amount_untaxed',
                                        help="This is the Total Amount for "
                                             "Food", tracking=5)
    amount_total_event = fields.Monetary(string="Total Amount for Event",
                                         compute='_compute_amount_untaxed',
                                         help="This is the Total Amount for "
                                              "Event", tracking=5)
    amount_total_service = fields.Monetary(string="Total Amount for Service",
                                           compute='_compute_amount_untaxed',
                                           help="This is the Total Amount for "
                                                "Service", tracking=5)
    amount_total_fleet = fields.Monetary(string="Total Amount for Fleet",
                                         compute='_compute_amount_untaxed',
                                         help="This is the Total Amount for "
                                              "Fleet", tracking=5)
    foto_ktp_file = fields.Binary(string="Upload Foto KTP")
    foto_ktp_filename = fields.Char("Nama File KTP")
    payment_method = fields.Char(string="Payment Method")
    booking_resource = fields.Char(string="Booking Resource")
    member_club = fields.Float(string="Member Club")
    assured_stay = fields.Float(string="Assured Stay")
    red_lite = fields.Float(string="Red Lite")
    platform_fee = fields.Float(string="Platform Fee")
    tip_staff = fields.Float(string="Tip For Staff")
    room_upgrade = fields.Float(string="Room Upgrade")
    early_late_co = fields.Boolean(string="Early CI/Late CO")
    travel_protection = fields.Boolean(string="Travel Protection")
    breakfast = fields.Boolean(string="Breakfast")
    keterangan = fields.Char(string="Keterangan")
    duration_nights = fields.Integer(string='Number of Nights', compute='_compute_duration', store=True)

    @api.depends('checkin_date', 'checkout_date')
    def _compute_duration(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                rec.duration_nights = (rec.checkout_date - rec.checkin_date).days or 1
            else:
                rec.duration_nights = 1

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'name' in fields:
            res['name'] = self.env['ir.sequence'].next_by_code('room.booking')
        return res

    @api.depends('partner_id')
    def _compute_user_id(self):
        """Computes the User id"""
        for order in self:
            order.user_id = \
                order.partner_id.address_get(['invoice'])[
                    'invoice'] if order.partner_id else False

    def _compute_invoice_count(self):
        """Compute the invoice count"""
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('ref', '=', self.name)])

    @api.depends('partner_id')
    def _compute_pricelist_id(self):
        """Computes PriceList"""
        for order in self:
            if not order.partner_id:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            order.pricelist_id = order.partner_id.property_product_pricelist

    @api.depends('room_line_ids.price_subtotal', 'room_line_ids.price_tax',
                 'room_line_ids.price_total',
                 'food_order_line_ids.price_subtotal',
                 'food_order_line_ids.price_tax',
                 'food_order_line_ids.price_total',
                 'service_line_ids.price_subtotal',
                 'service_line_ids.price_tax', 'service_line_ids.price_total',
                 'vehicle_line_ids.price_subtotal',
                 'vehicle_line_ids.price_tax', 'vehicle_line_ids.price_total',
                 'event_line_ids.price_subtotal', 'event_line_ids.price_tax',
                 'event_line_ids.price_total',
                 )
    def _compute_amount_untaxed(self, flag=False):
        """Compute total amounts for each booking and generate booking_list for invoice"""
        booking_all_list = []
        for booking in self:
            amount_untaxed_room = 0.0
            amount_untaxed_food = 0.0
            amount_untaxed_fleet = 0.0
            amount_untaxed_event = 0.0
            amount_untaxed_service = 0.0
            amount_taxed_room = 0.0
            amount_taxed_food = 0.0
            amount_taxed_fleet = 0.0
            amount_taxed_event = 0.0
            amount_taxed_service = 0.0
            amount_total_room = 0.0
            amount_total_food = 0.0
            amount_total_fleet = 0.0
            amount_total_event = 0.0
            amount_total_service = 0.0
            booking_list = []

            account_move_line = booking.env['account.move.line'].search_read(
                domain=[('ref', '=', booking.name),
                        ('display_type', '!=', 'payment_term')],
                fields=['name', 'quantity', 'price_unit', 'product_type'],
            )
            for rec in account_move_line:
                rec.pop('id', None)

            if booking.room_line_ids:
                amount_untaxed_room += sum(booking.room_line_ids.mapped('price_subtotal'))
                amount_taxed_room += sum(booking.room_line_ids.mapped('price_tax'))
                amount_total_room += sum(booking.room_line_ids.mapped('price_total'))
                for room in booking.room_line_ids:
                    booking_dict = {
                        'name': room.room_id.name,
                        'quantity': room.uom_qty,
                        'price_unit': room.price_unit,
                        'product_type': 'room'
                    }
                    if booking_dict not in account_move_line:
                        if not account_move_line:
                            booking_list.append(booking_dict)
                        else:
                            for rec in account_move_line:
                                if rec['product_type'] == 'room' and booking_dict['name'] == rec['name'] \
                                        and booking_dict['price_unit'] == rec['price_unit'] \
                                        and booking_dict['quantity'] != rec['quantity']:
                                    booking_list.append({
                                        'name': room.room_id.name,
                                        'quantity': booking_dict['quantity'] - rec['quantity'],
                                        'price_unit': room.price_unit,
                                        'product_type': 'room'
                                    })
                                else:
                                    booking_list.append(booking_dict)
                    if flag:
                        room.booking_line_visible = True

            if booking.food_order_line_ids:
                for food in booking.food_order_line_ids:
                    booking_list.append(booking.create_list(food))
                amount_untaxed_food += sum(booking.food_order_line_ids.mapped('price_subtotal'))
                amount_taxed_food += sum(booking.food_order_line_ids.mapped('price_tax'))
                amount_total_food += sum(booking.food_order_line_ids.mapped('price_total'))

            if booking.service_line_ids:
                for service in booking.service_line_ids:
                    booking_list.append(booking.create_list(service))
                amount_untaxed_service += sum(booking.service_line_ids.mapped('price_subtotal'))
                amount_taxed_service += sum(booking.service_line_ids.mapped('price_tax'))
                amount_total_service += sum(booking.service_line_ids.mapped('price_total'))

            if booking.vehicle_line_ids:
                for fleet in booking.vehicle_line_ids:
                    booking_list.append(booking.create_list(fleet))
                amount_untaxed_fleet += sum(booking.vehicle_line_ids.mapped('price_subtotal'))
                amount_taxed_fleet += sum(booking.vehicle_line_ids.mapped('price_tax'))
                amount_total_fleet += sum(booking.vehicle_line_ids.mapped('price_total'))

            if booking.event_line_ids:
                for event in booking.event_line_ids:
                    booking_list.append(booking.create_list(event))
                amount_untaxed_event += sum(booking.event_line_ids.mapped('price_subtotal'))
                amount_taxed_event += sum(booking.event_line_ids.mapped('price_tax'))
                amount_total_event += sum(booking.event_line_ids.mapped('price_total'))

            booking.amount_untaxed = amount_untaxed_room + amount_untaxed_food + amount_untaxed_fleet + amount_untaxed_event + amount_untaxed_service
            booking.amount_untaxed_food = amount_untaxed_food
            booking.amount_untaxed_room = amount_untaxed_room
            booking.amount_untaxed_fleet = amount_untaxed_fleet
            booking.amount_untaxed_event = amount_untaxed_event
            booking.amount_untaxed_service = amount_untaxed_service

            booking.amount_tax = amount_taxed_food + amount_taxed_room + amount_taxed_fleet + amount_taxed_event + amount_taxed_service
            booking.amount_taxed_food = amount_taxed_food
            booking.amount_taxed_room = amount_taxed_room
            booking.amount_taxed_fleet = amount_taxed_fleet
            booking.amount_taxed_event = amount_taxed_event
            booking.amount_taxed_service = amount_taxed_service

            booking.amount_total = amount_total_food + amount_total_room + amount_total_fleet + amount_total_event + amount_total_service
            booking.amount_total_food = amount_total_food
            booking.amount_total_room = amount_total_room
            booking.amount_total_fleet = amount_total_fleet
            booking.amount_total_event = amount_total_event
            booking.amount_total_service = amount_total_service

            booking_all_list += booking_list

        return booking_all_list

    @api.onchange('need_food')
    def _onchange_need_food(self):
        """Unlink Food Booking Line if Need Food is false"""
        if not self.need_food and self.food_order_line_ids:
            for food in self.food_order_line_ids:
                food.unlink()

    @api.onchange('need_service')
    def _onchange_need_service(self):
        """Unlink Service Booking Line if Need Service is False"""
        if not self.need_service and self.service_line_ids:
            for serv in self.service_line_ids:
                serv.unlink()

    @api.onchange('need_fleet')
    def _onchange_need_fleet(self):
        """Unlink Fleet Booking Line if Need Fleet is False"""
        if not self.need_fleet:
            if self.vehicle_line_ids:
                for fleet in self.vehicle_line_ids:
                    fleet.unlink()

    @api.onchange('need_event')
    def _onchange_need_event(self):
        """Unlink Event Booking Line if Need Event is False"""
        if not self.need_event:
            if self.event_line_ids:
                for event in self.event_line_ids:
                    event.unlink()

    @api.onchange('food_order_line_ids', 'room_line_ids',
                  'service_line_ids', 'vehicle_line_ids', 'event_line_ids')
    def _onchange_room_line_ids(self):
        """Invokes the Compute amounts function"""
        self._compute_amount_untaxed()
        self.invoice_button_visible = False

    @api.constrains("room_line_ids")
    def _check_duplicate_folio_room_line(self):
        """
        This method is used to validate the room_lines.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for record in self:
            # Create a set of unique ids
            ids = set()
            for line in record.room_line_ids:
                if line.room_id.id in ids:
                    raise ValidationError(
                        _(
                            """Room Entry Duplicates Found!, """
                            """You Cannot Book "%s" Room More Than Once!"""
                        )
                        % line.room_id.name
                    )
                ids.add(line.room_id.id)

    def create_list(self, line_ids):
        """Returns a Dictionary containing the Booking line Values"""
        account_move_line = self.env['account.move.line'].search_read(
            domain=[('ref', '=', self.name),
                    ('display_type', '!=', 'payment_term')],
            fields=['name', 'quantity', 'price_unit', 'product_type'], )
        for rec in account_move_line:
            del rec['id']
        booking_dict = {}
        for line in line_ids:
            name = ""
            product_type = ""
            if line_ids._name == 'food.booking.line':
                name = line.food_id.name
                product_type = 'food'
            elif line_ids._name == 'fleet.booking.line':
                name = line.fleet_id.name
                product_type = 'fleet'
            elif line_ids._name == 'service.booking.line':
                name = line.service_id.name
                product_type = 'service'
            elif line_ids._name == 'event.booking.line':
                name = line.event_id.name
                product_type = 'event'
            booking_dict = {'name': name,
                            'quantity': line.uom_qty,
                            'price_unit': line.price_unit,
                            'product_type': product_type}
        return booking_dict

    def action_reserve(self):
        """Button Reserve Function"""
        ROOM_TYPE_PERSON_MAP = {

            'redDoorz Room': 1,
            'redDoorz Deluxe Twin Room': 2,
            'redDoorz Deluxe Room': 4,
            'family Room': 4,

            'single': 1,
            'double': 2,
            'dormitory': 4,

        }

        if self.state == 'reserved':
            message = _("Room Already Reserved.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': message,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        if self.room_line_ids:
            for room in self.room_line_ids:
                if room.room_id:
                    # Ambil nilai sinkron dari booking line
                    synced_type = room.room_type or room.room_id.room_type
                    synced_persons = ROOM_TYPE_PERSON_MAP.get(synced_type, 1)

                    # Update ke hotel.room
                    room.room_id.write({
                        'status': 'reserved',
                        'room_type': synced_type,
                        'num_person': synced_persons,
                        'is_room_avail': False,
                    })

            self.write({"state": "reserved"})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Rooms reserved Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                    'reload': True,  # supaya kanban ikut update
                }
            }

        raise ValidationError(_("Please Enter Room Details."))

    def action_cancel(self):
        """
        @param self: object pointer
        """
        if self.room_line_ids:
            for room in self.room_line_ids:
                room.room_id.write({
                    'status': 'available',
                })
                room.room_id.is_room_avail = True
        self.write({"state": "cancel"})

    def action_maintenance_request(self):
        """
        Function that handles the maintenance request
        """
        room_list = []
        for rec in self.room_line_ids.room_id.ids:
            room_list.append(rec)
        if room_list:
            room_id = self.env['hotel.room'].search([
                ('id', 'in', room_list)])
            self.env['maintenance.request'].sudo().create({
                'date': fields.Date.today(),
                'state': 'draft',
                'type': 'room',
                'room_maintenance_ids': room_id.ids,
            })
            self.maintenance_request_sent = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Maintenance Request Sent Successfully",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        raise ValidationError(_("Please Enter Room Details"))

    def action_done(self):
        """Button action_confirm function"""
        for rec in self.env['account.move'].search(
                [('ref', '=', self.name)]):
            if rec.payment_state != 'not_paid':
                self.write({"state": "done"})
                self.is_checkin = False
                if self.room_line_ids:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'success',
                            'message': "Booking Checked Out Successfully!",
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }
            raise ValidationError(_('Your Invoice is Due for Payment.'))
        self.write({"state": "done"})

    from datetime import datetime

    def action_checkout(self):
        """Button action_check_out function"""
        self.write({"state": "check_out"})
        for room in self.room_line_ids:
            room.room_id.write({
                'status': 'available',
                'is_room_avail': True,
                'clean_status': 'dirty',  # ✅ TAMBAHAN agar status jadi 'dirty'
            })
            room.write({'checkout_date': datetime.today()})

    def action_invoice(self):
        """Method for creating invoice"""
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        booking_list = self._compute_amount_untaxed(True)
        if booking_list:
            account_move = self.env["account.move"].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                'ref': self.name,
            }])
            for rec in booking_list:
                account_move.invoice_line_ids.create([{
                    'name': rec['name'],
                    'quantity': rec['quantity'],
                    'price_unit': rec['price_unit'],
                    'move_id': account_move.id,
                    'price_subtotal': rec['quantity'] * rec['price_unit'],
                    'product_type': rec['product_type'],
                }])
            self.write({'invoice_status': "invoiced"})
            self.invoice_button_visible = True
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.move',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_id': account_move.id,
                'context': "{'create': False}"
            }

    def toggle_ktp_received(self):
        """Button to mark KTP as received"""
        for rec in self:
            rec.ktp_received = True

    def toggle_deposit_received(self):
        """Button to mark Deposit as received"""
        for rec in self:
            rec.deposit_received = True

    def action_view_invoices(self):
        """Method for Returning invoice View"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'list,form',
            'view_type': 'list,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name)],
            'context': "{'create': False}"
        }

    def action_checkin(self):
        """
        @param self: object pointer
        """
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        else:
            for room in self.room_line_ids:
                room.room_id.write({
                    'status': 'occupied',
                })
                room.room_id.is_room_avail = False
            self.write({"state": "check_in"})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Booking Checked In Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

    @api.constrains('ktp', 'deposit')
    def _check_ktp_deposit(self):
        if self.env.context.get('skip_cek_validasi'):
            return
        for rec in self:
            if not rec.ktp or not rec.deposit:
                raise ValidationError("Mohon pastikan KTP dan Deposit telah diterima sebelum menyimpan.")

    def get_details(self):
        """ Returns different counts for displaying in dashboard"""
        today = datetime.today()
        tz_name = self.env.user.tz
        today_utc = pytz.timezone('UTC').localize(today,
                                                  is_dst=False)
        context_today = today_utc.astimezone(pytz.timezone(tz_name))
        total_room = self.env['hotel.room'].search_count([])
        check_in = self.env['room.booking'].search_count(
            [('state', '=', 'check_in')])
        available_room = self.env['hotel.room'].search(
            [('status', '=', 'available')])
        reservation = self.env['room.booking'].search_count(
            [('state', '=', 'reserved')])
        check_outs = self.env['room.booking'].search([])
        check_out = 0
        staff = 0
        for rec in check_outs:
            for room in rec.room_line_ids:
                if room.checkout_date.date() == context_today.date():
                    check_out += 1
            """staff"""
            staff = self.env['res.users'].search_count(
                [('groups_id', 'in',
                  [self.env.ref('hotel_management_odoo.hotel_group_admin').id,
                   self.env.ref(
                       'hotel_management_odoo.cleaning_team_group_head').id,
                   self.env.ref(
                       'hotel_management_odoo.cleaning_team_group_user').id,
                   self.env.ref(
                       'hotel_management_odoo.hotel_group_reception').id,
                   self.env.ref(
                       'hotel_management_odoo.maintenance_team_group_leader').id,
                   self.env.ref(
                       'hotel_management_odoo.maintenance_team_group_user').id
                   ])])
        total_vehicle = self.env['fleet.vehicle.model'].search_count([])
        available_vehicle = total_vehicle - self.env[
            'fleet.booking.line'].search_count(
            [('state', '=', 'check_in')])
        total_event = self.env['event.event'].search_count([])
        pending_event = self.env['event.event'].search([])
        pending_events = 0
        today_events = 0
        for pending in pending_event:
            if pending.date_end >= fields.datetime.now():
                pending_events += 1
            if pending.date_end.date() == fields.date.today():
                today_events += 1
        food_items = self.env['lunch.product'].search_count([])
        food_order = len(self.env['food.booking.line'].search([]).filtered(
            lambda r: r.booking_id.state not in ['check_out', 'cancel',
                                                 'done']))
        """total Revenue"""
        total_revenue = 0
        today_revenue = 0
        pending_payment = 0
        for rec in self.env['account.move'].search(
                [('payment_state', '=', 'paid')]):
            if rec.ref:
                if 'BOOKING' in rec.ref:
                    total_revenue += rec.amount_total
                    if rec.date == fields.date.today():
                        today_revenue += rec.amount_total
        for rec in self.env['account.move'].search(
                [('payment_state', '=', 'not_paid')]):
            if rec.ref:
                if 'BOOKING' in rec.ref:
                    pending_payment += rec.amount_total
        return {
            'total_room': total_room,
            'available_room': len(available_room),
            'staff': staff,
            'check_in': check_in,
            'reservation': reservation,
            'check_out': check_out,
            'total_vehicle': total_vehicle,
            'available_vehicle': available_vehicle,
            'total_event': total_event,
            'today_events': today_events,
            'pending_events': pending_events,
            'food_items': food_items,
            'food_order': food_order,
            'total_revenue': round(total_revenue, 2),
            'today_revenue': round(today_revenue, 2),
            'pending_payment': round(pending_payment, 2),
            'currency_symbol': self.env.user.company_id.currency_id.symbol,
            'currency_position': self.env.user.company_id.currency_id.position
        }

    def action_print_booking(self):
        return self.env.ref('hotel_management_odoo.action_report_room_booking').report_action(self)

    @api.model
    def create(self, vals):
        # Jangan validasi KTP dan Deposit di sini
        return super(RoomBooking, self).create(vals)

    def write(self, vals):
        # Jangan validasi KTP dan Deposit di sini
        return super(RoomBooking, self).write(vals)

    def action_cek(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.room',
            'view_mode': 'kanban',
            'target': 'current',
            'name': 'Room Chart',
        }


