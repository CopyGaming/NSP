from odoo import models, fields, tools

class HotelRoomDashboard(models.Model):
    _name = 'hotel.room.dashboard'
    _description = 'Dashboard Ketersediaan Kamar'
    _auto = False  # karena model ini hanya view, bukan tabel asli

    room_name = fields.Char(string='Nama Kamar')
    status = fields.Selection([
        ('available', 'Available'),
        ('booked', 'Booked')
    ], string='Status')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hotel_room_dashboard AS (
                SELECT
                    r.id AS id,
                    r.name AS room_name,
                    CASE
                        WHEN r.is_booked = TRUE THEN 'booked'
                        ELSE 'available'
                    END AS status
                FROM hotel_room r
            )
        """)
