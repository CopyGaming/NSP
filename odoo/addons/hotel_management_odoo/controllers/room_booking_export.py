from odoo import http
from odoo.http import request
import io
from datetime import datetime
from odoo.tools.misc import xlsxwriter

class RoomBookingExportController(http.Controller):

    @http.route('/download/room_booking_excel', type='http', auth="user", csrf=False)
    def download_room_booking_excel(self, **kwargs):
        active_ids_str = kwargs.get('active_ids', '')
        active_ids = [int(x) for x in active_ids_str.split(',') if x.strip().isdigit()]
        domain = [('id', 'in', active_ids)] if active_ids else []
        bookings = request.env['room.booking'].sudo().search(domain)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Laporan Setoran')

        # Format
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'
        })
        cell_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0', 'align': 'right'})
        center_format = workbook.add_format({'border': 1, 'align': 'center'})

        # Set column widths
        sheet.set_column('A:A', 5)   # No
        sheet.set_column('B:B', 20)  # Guest Name
        sheet.set_column('C:D', 12)  # Checkin - Checkout
        sheet.set_column('E:E', 6)   # Rooms
        sheet.set_column('F:F', 6)   # Night
        sheet.set_column('G:G', 20)  # Room Type
        sheet.set_column('H:P', 12)
        sheet.set_column('Q:Q', 15)  # Total Amount
        sheet.set_column('R:R', 12)  # Payment Method
        sheet.set_column('S:S', 18)  # Booking Resource
        sheet.set_column('T:T', 10)  # Keterangan

        # Judul
        sheet.merge_range('A1:T1', 'Laporan Setoran Guest House Dipatiukur', title_format)
        sheet.merge_range('A2:T2', 'Tanggal : Jumat 18 JULI 2025', title_format)

        # Header
        headers = [
            'No', 'Guest Name', 'Check In Date', 'Check Out Date', 'Rooms', 'Night', 'Room Type',
            'IDR', 'Early CI/Late CO', 'Travel Protection', 'Breakfast', 'Member Club',
            'Assured Stay', 'Red Lite', 'Platform Fee', 'Tip For Staff', 'Room Upgrade',
            'Total PAH', 'Total Amount', 'Payment Method', 'Booking Resource', 'Keterangan'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(2, col_num, header, header_format)

        # Isi Data
        for idx, booking in enumerate(bookings, start=1):
            row = 2 + idx
            guest = booking.partner_id.name
            checkin = booking.checkin_date.strftime('%d/%m/%Y') if booking.checkin_date else ''
            checkout = booking.checkout_date.strftime('%d/%m/%Y') if booking.checkout_date else ''
            nights = booking.duration_nights or 1
            room_type = booking.room_line_ids[0].room_id.room_type if booking.room_line_ids else ''
            total_amount = booking.amount_total or 0
            booking_res = booking.booking_resource or ''
            keterangan = booking.state.capitalize()

            # Contoh dummy asumsi data (harus diganti dengan field yang sesuai)
            sheet.write(row, 0, idx, center_format)
            sheet.write(row, 1, guest, cell_format)
            sheet.write(row, 2, checkin, center_format)
            sheet.write(row, 3, checkout, center_format)
            sheet.write(row, 4, 1, center_format)
            sheet.write(row, 5, nights, center_format)
            sheet.write(row, 6, room_type, cell_format)
            sheet.write(row, 7, 'IDR', center_format)
            sheet.write(row, 8, '', cell_format)  # Early CI/CO
            sheet.write(row, 9, '', cell_format)  # Travel Protection
            sheet.write(row,10, '', cell_format)  # Breakfast
            sheet.write(row,11, '', cell_format)  # Member Club
            sheet.write(row,12, '', cell_format)  # Assured Stay
            sheet.write(row,13, '', cell_format)  # Red Lite
            sheet.write(row,14, '', cell_format)  # Platform Fee
            sheet.write(row,15, '', cell_format)  # Tip for Staff
            sheet.write(row,16, '', cell_format)  # Room Upgrade
            sheet.write(row,17, '', cell_format)  # Total PAH
            sheet.write(row,18, total_amount, money_format)  # Total Amount
            sheet.write(row,19, booking.payment_method or '', center_format)
            sheet.write(row,20, booking_res, cell_format)
            sheet.write(row,21, keterangan, center_format)

        workbook.close()
        output.seek(0)

        filename = f"Laporan_Setoran_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
