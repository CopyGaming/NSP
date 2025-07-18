from odoo import http
from odoo.http import request
import io
from datetime import datetime
from odoo.tools.misc import xlsxwriter

class RoomBookingExportController(http.Controller):

    @http.route('/download/room_booking_excel', type='http', auth="user", csrf=False)
    def download_room_booking_excel(self, **kwargs):
        bookings = request.env['room.booking'].sudo().search([])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Room Bookings')

        # Format styles
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter', 'border': 1
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'
        })
        cell_format = workbook.add_format({'border': 1})

        # Set width
        sheet.set_column('A:F', 20)

        # Baris 1: Judul
        sheet.merge_range('A1:F1', 'Booking Room Report', title_format)

        # Baris 2: Header kolom
        headers = ['Booking Number', 'Customer', 'Check-in', 'Check-out', 'Room', 'Status']
        for col_num, header in enumerate(headers):
            sheet.write(1, col_num, header, header_format)

        # Baris 3 dst: Data
        for row_num, booking in enumerate(bookings, start=2):
            room_name = booking.room_line_ids[0].room_id.name if booking.room_line_ids else ''
            sheet.write(row_num, 0, booking.name or '', cell_format)
            sheet.write(row_num, 1, booking.partner_id.name or '', cell_format)
            sheet.write(row_num, 2, str(booking.checkin_date or ''), cell_format)
            sheet.write(row_num, 3, str(booking.checkout_date or ''), cell_format)
            sheet.write(row_num, 4, room_name, cell_format)
            sheet.write(row_num, 5, booking.state or '', cell_format)

        workbook.close()
        output.seek(0)

        filename = 'Room_Booking_Report_%s.xlsx' % datetime.now().strftime('%Y%m%d_%H%M%S')
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
