from odoo import models

class SaleOrderExcelReport(models.AbstractModel):
    _name = 'report.your_module.sale_order_excel_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Sale Orders')
        bold = workbook.add_format({'bold': True})

        headers = ['Order Name', 'Customer', 'Order Date', 'Total']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        row = 1
        for order in wizard.order_ids:
            sheet.write(row, 0, order.name)
            sheet.write(row, 1, order.partner_id.name)
            sheet.write(row, 2, str(order.date_order))
            sheet.write(row, 3, order.amount_total)
            row += 1
