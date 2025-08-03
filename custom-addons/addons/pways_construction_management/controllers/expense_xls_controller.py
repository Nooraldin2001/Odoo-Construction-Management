from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
from datetime import datetime


class VoucherxlsReport(http.Controller):
    @http.route(['/project/expense_xls_report/<int:project_id>'], type='http', auth="user", csrf=False)
    def get_expense_xls_rprt(self, project_id=None, **args):
        model = request.env['project.project'].browse(project_id)    
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Expense XLS Report' + '.xlsx'))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Define styles
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format({'font_name': 'Times', 'bold': True, 'align': 'center'})
        header_text_style = workbook.add_format({'font_name': 'Times', 'bold': True,'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center', 'bold': True})
        number_style = workbook.add_format({'font_name': 'Times', 'align': 'center', 'num_format': '0.00'})
        total_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center', 'num_format': '0.00'})
        font_style = workbook.add_format({'font_name': 'Times', 'align': 'center'})

        # Define sheet names
        sheet_names = ['Project', 'Materials', 'Labours Sheet', 'Overhead', 'Bills']

        # Create and format each sheet
        for sheet_name in sheet_names:
            sheet = workbook.add_worksheet(sheet_name)
            sheet.set_landscape()
            sheet.set_paper(9)
            sheet.set_margins(0.5, 0.5, 0.5, 0.5)

            # Column widths
            columns = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
            for col in columns:
                sheet.set_column(f'{col}:{col}', 18)

            # Report title
            sheet.merge_range('A2:F2', f'{sheet_name} Report', title_style)

            ############# Project #############
            row = 4
            if sheet_name == 'Project':
                # ======Material======
                sheet.merge_range('A4:C4', 'Material Details', header_text_style)
                row += 1

                # Headers
                sheet.write(row, 1, 'Purchase', header_style)
                sheet.write(row, 2, 'Move', header_style)
                sheet.write(row, 3, 'Consumed', header_style)
                row += 1

                # Totals
                total_purchase_qty = 0.00
                total_purchase_price = 0.00
                total_stock_picking_qty = 0.00
                total_stock_picking_price = 0.00
                total_consumed_qty = 0.00
                total_consumed_price = 0.00

                for project in model:
                    for task in project.task_ids:
                        purchase_requisition_ids = request.env['material.purchase.requisition'].search([('task_id', '=', task.id)])
                        purchase_ids = request.env['purchase.order'].search([('custom_requisition_id', 'in', purchase_requisition_ids.ids)])
                        picking_ids = request.env['stock.picking'].search([('custom_requisition_id', 'in', purchase_requisition_ids.ids)])
                        consumed_material_ids = task.consumed_material_ids

                        # Gather all products involved
                        all_products = set()
                        for consumed in consumed_material_ids:
                            all_products.add(consumed.product_id.id)

                        for purchase in purchase_ids:
                            for po_line in purchase.order_line:
                                all_products.add(po_line.product_id.id)

                        for picking_id in picking_ids:
                            for picking_move in picking_id.move_ids:
                                all_products.add(picking_move.product_id.id)

                        for product_id in all_products:
                            product = request.env['product.product'].browse(product_id)

                            # Initialize quantities and prices
                            purchase_qty = 0.00
                            purchase_price = 0.00
                            stock_picking_qty = 0.00
                            stock_picking_price = 0.00
                            consumed_qty = 0.00
                            consumed_price = 0.00

                            # Find corresponding purchase order for the product
                            purchase_order = next((po for po in purchase_ids if product.id in po.order_line.mapped('product_id.id')), None)
                            if purchase_order:
                                # Sum quantities and prices from purchase order lines
                                purchase_qty = sum(po_line.product_qty for po_line in purchase_order.order_line if po_line.product_id.id == product.id)
                                purchase_price = sum(po_line.product_id.lst_price * po_line.product_qty for po_line in purchase_order.order_line if po_line.product_id.id == product.id)

                            # Find corresponding purchase order for the product
                            stock_picking = next((pick for pick in picking_ids if product.id in pick.move_ids.mapped('product_id.id')), None)
                            if stock_picking:
                                stock_picking_qty = sum(move.product_qty for move in stock_picking.move_ids if move.product_id.id == product.id)
                                stock_picking_price = sum(move.product_id.lst_price * move.product_qty for move in stock_picking.move_ids if move.product_id.id == product.id)
                            
                            # Find consumed quantity and list price for the product
                            for consumed in consumed_material_ids.filtered(lambda c: c.product_id.id == product.id):
                                consumed_qty += consumed.product_uom_qty
                                consumed_price += consumed.product_id.lst_price * consumed.product_uom_qty

                            # Add to totals
                            total_purchase_qty += purchase_qty
                            total_purchase_price += purchase_price
                            total_stock_picking_qty += stock_picking_qty
                            total_stock_picking_price += stock_picking_price
                            total_consumed_qty += consumed_qty
                            total_consumed_price += consumed_price

                # Write totals to the cells
                sheet.write(row, 0, 'Qty', header_style)
                sheet.write(row, 1, total_purchase_qty, number_style)
                sheet.write(row, 2, total_stock_picking_qty, number_style)
                sheet.write(row, 3, total_consumed_qty, number_style)
                row += 1

                sheet.write(row, 0, 'Price', header_style)
                sheet.write(row, 1, total_purchase_price, number_style)
                sheet.write(row, 2, total_stock_picking_price, number_style)
                sheet.write(row, 3, total_consumed_price, number_style)
                row += 3

                # ======Labours======
                sheet.merge_range(f'A{row}:C{row}', 'Labours Details', header_text_style)
                row += 1
                labours_total_subtotals = 0.00
                labours_total_spent_hrs = 0.00

                for project in model:
                    for task in project.task_ids:
                        for timesheet_id in task.timesheet_ids:
                            subtotals = timesheet_id.employee_id.price_per_time * timesheet_id.unit_amount
                            labours_total_subtotals += subtotals
                            labours_total_spent_hrs += timesheet_id.unit_amount

                sheet.write(row, 0, 'Qty', header_style)
                sheet.write(row, 1, labours_total_spent_hrs, number_style)
                row += 1
                sheet.write(row, 0, 'Price', header_style)
                sheet.write(row, 1, labours_total_subtotals, number_style)
                row += 3

                # ======Overhead======
                sheet.merge_range(f'A{row}:C{row}', 'Overhead Details', header_text_style)
                row += 2
                total_vehicle_qty = 0.00
                total_equipment_qty = 0.00
                total_expense = 0.00

                for project in model:
                    for task in project.task_ids:
                        for req_vehcle_line_id in task.req_vehcle_line_ids:
                            total_vehicle_qty += req_vehcle_line_id.hours
                        for req_equipment_line_id in task.req_equipment_line_ids:
                            total_equipment_qty += req_equipment_line_id.hours
                        for expense_id in task.expense_ids:
                            total_expense += expense_id.total_amount

                sheet.merge_range(f'A{row}:C{row}', 'Vehicle', title_style)
                sheet.write(row, 0, 'Qty', header_style)
                sheet.write(row, 1, total_vehicle_qty, number_style)
                # row += 1
                row += 3

                sheet.merge_range(f'A{row}:C{row}', 'Equipments', title_style)
                sheet.write(row, 0, 'Qty', header_style)
                sheet.write(row, 1, total_equipment_qty, number_style)
                # row += 1
                row += 3

                sheet.merge_range(f'A{row}:C{row}', 'Expenses', title_style)
                sheet.write(row, 0, 'Total Expenses', header_style)
                sheet.write(row, 1, total_expense, number_style)
                row += 3

                # ======Bills======
                sheet.merge_range(f'A{row}:C{row}', 'Bills Details', header_text_style)
                row += 1
                total_bills_qty = 0.00
                total_bills_price = 0.00

                for project in model:
                    for task in project.task_ids:
                        bill_ids = request.env['account.move'].search([('task_id', '=', task.id)])
                        for bill_id in bill_ids:
                            for invoice_line_id in bill_id.invoice_line_ids:
                                total_bills_qty += invoice_line_id.quantity
                                total_bills_price += invoice_line_id.price_subtotal

                sheet.write(row, 0, 'Qty', header_style)
                sheet.write(row, 1, total_bills_qty, number_style)
                row += 1
                sheet.write(row, 0, 'Price', header_style)
                sheet.write(row, 1, total_bills_price, number_style)
                row += 3

                # ======Final Total======
                sheet.merge_range(f'A{row}:C{row}', 'Final Total', header_text_style)
                row += 1
                final_total_qty = 0.00
                final_total_price = 0.00

                final_total_qty = total_purchase_qty + total_stock_picking_qty + total_consumed_qty + total_vehicle_qty + total_equipment_qty + total_bills_qty + labours_total_spent_hrs
                final_total_price = total_purchase_price + total_stock_picking_price + total_consumed_price + labours_total_subtotals + total_expense + total_bills_price

                sheet.write(row, 0, 'Qty', header_style)
                sheet.write(row, 1, final_total_qty, total_style)
                row += 1
                sheet.write(row, 0, 'Price', header_style)
                sheet.write(row, 1, final_total_price, total_style)
                row += 3

            ############# Materials #############
            row = 4
            if sheet_name == 'Materials':
                main_headers = ['Product', 'Unit Price', 'Purchase', '', 'Moved', '', 'Consumed', '']
                sheet.write_row('A6', main_headers, header_style)
                row += 1

                sheet.merge_range('C6:D6', 'Purchase', header_style)
                sheet.merge_range('E6:F6', 'Move', header_style)
                sheet.merge_range('G6:H6', 'Consumed', header_style)

                sub_headers = ['Qty', 'Price', 'Qty', 'Price', 'Qty', 'Price']
                sheet.write_row('C7', sub_headers, header_style)

                row += 2

                total_purchase_qty = 0.00
                total_purchase_price = 0.00
                total_stock_picking_qty = 0.00
                total_stock_picking_price = 0.00
                total_consumed_qty = 0.00
                total_consumed_price = 0.00

                for project in model:
                    for task in project.task_ids:
                        purchase_requisition_ids = request.env['material.purchase.requisition'].search([('task_id', '=', task.id)])
                        purchase_ids = request.env['purchase.order'].search([('custom_requisition_id', 'in', purchase_requisition_ids.ids)])
                        picking_ids = request.env['stock.picking'].search([('custom_requisition_id', 'in', purchase_requisition_ids.ids)])
                        consumed_material_ids = task.consumed_material_ids

                        # Gather all products involved
                        all_products = set()
                        for consumed in consumed_material_ids:
                            all_products.add(consumed.product_id.id)

                        for purchase in purchase_ids:
                            for po_line in purchase.order_line:
                                all_products.add(po_line.product_id.id)

                        for picking_id in picking_ids:
                            for picking_move in picking_id.move_ids:
                                all_products.add(picking_move.product_id.id)

                        for product_id in all_products:
                            product = request.env['product.product'].browse(product_id)

                            # Initialize quantities and prices
                            purchase_qty = 0.00
                            purchase_price = 0.00
                            stock_picking_qty = 0.00
                            stock_picking_price = 0.00
                            consumed_qty = 0.00
                            consumed_price = 0.00

                            # Find corresponding purchase order for the product
                            purchase_order = next((po for po in purchase_ids if product.id in po.order_line.mapped('product_id.id')), None)
                            if purchase_order:
                                # Sum quantities and prices from purchase order lines
                                purchase_qty = sum(po_line.product_qty for po_line in purchase_order.order_line if po_line.product_id.id == product.id)
                                purchase_price = sum(po_line.product_id.lst_price * po_line.product_qty for po_line in purchase_order.order_line if po_line.product_id.id == product.id)

                            # Find corresponding purchase order for the product
                            stock_picking = next((pick for pick in picking_ids if product.id in pick.move_ids.mapped('product_id.id')), None)
                            if stock_picking:
                                stock_picking_qty = sum(move.product_qty for move in stock_picking.move_ids if move.product_id.id == product.id)
                                stock_picking_price = sum(move.product_id.lst_price * move.product_qty for move in stock_picking.move_ids if move.product_id.id == product.id)
                            
                            # Find consumed quantity and list price for the product
                            for consumed in consumed_material_ids.filtered(lambda c: c.product_id.id == product.id):
                                consumed_qty += consumed.product_uom_qty
                                consumed_price += consumed.product_id.lst_price * consumed.product_uom_qty

                            # Write to Excel
                            sheet.write(row, 0, product.display_name, font_style)
                            sheet.write(row, 1, product.lst_price, number_style)
                            sheet.write(row, 2, purchase_qty, number_style)
                            sheet.write(row, 3, purchase_price, number_style)
                            sheet.write(row, 4, stock_picking_qty if stock_picking_qty > 0 else 0.00, number_style)
                            sheet.write(row, 5, stock_picking_price if stock_picking_price > 0 else 0.00, number_style)
                            sheet.write(row, 6, consumed_qty if consumed_qty > 0 else 0.00, number_style)
                            sheet.write(row, 7, consumed_price if consumed_price > 0 else 0.00, number_style)
                            
                            # Add to totals
                            total_purchase_qty += purchase_qty
                            total_purchase_price += purchase_price
                            total_stock_picking_qty += stock_picking_qty
                            total_stock_picking_price += stock_picking_price
                            total_consumed_qty += consumed_qty
                            total_consumed_price += consumed_price
                            
                            row += 1

                # Write totals to the last row
                sheet.write(row, 0, 'Total', header_style)
                sheet.write(row, 2, total_purchase_qty, total_style)
                sheet.write(row, 3, total_purchase_price, total_style)
                sheet.write(row, 4, total_stock_picking_qty, total_style)
                sheet.write(row, 5, total_stock_picking_price, total_style)
                sheet.write(row, 6, total_consumed_qty, total_style)
                sheet.write(row, 7, total_consumed_price, total_style)

            ############# Labours Sheet #############
            row = 4
            if sheet_name == 'Labours Sheet':
                headers = ['Task', 'Date', 'Employee', 'Description', 'Hours Spent', 'Salary Period', 'Price/Time', 'Subtotals']
                for col_num, header in enumerate(headers):
                    sheet.write(row, col_num, header, header_style)
                row += 2

                labours_total_subtotals = 0.00
                labours_total_spent_hrs = 0.00

                for project in model:
                    for task in project.task_ids:
                        for timesheet_id in task.timesheet_ids:
                            sheet.write(row, 0, task.name, font_style)
                            sheet.write(row, 1, timesheet_id.date.strftime("%d-%m-%Y"), font_style)
                            sheet.write(row, 2, timesheet_id.employee_id.display_name, font_style)
                            sheet.write(row, 3, timesheet_id.name, font_style)
                            sheet.write(row, 4, timesheet_id.unit_amount, number_style)
                            if timesheet_id.employee_id.salary_period == 'hours':
                                sheet.write(row, 5, 'Hours', font_style)
                            if timesheet_id.employee_id.salary_period == 'days':
                                sheet.write(row, 5, 'Days', font_style)
                            if timesheet_id.employee_id.salary_period == 'months':
                                sheet.write(row, 5, 'Months', font_style)
                            
                            sheet.write(row, 6, timesheet_id.employee_id.price_per_time, number_style)
                            
                            # Compute Subtotals
                            subtotals = timesheet_id.employee_id.price_per_time * timesheet_id.unit_amount
                            sheet.write(row, 7, subtotals, number_style)
                            labours_total_subtotals += subtotals
                            labours_total_spent_hrs += timesheet_id.unit_amount
                            row += 1

                # Write total subtotals to the last row
                sheet.write(row, 0, 'Total', header_style)
                sheet.write(row, 4, labours_total_spent_hrs, total_style)
                sheet.write(row, 7, labours_total_subtotals, total_style)

            ############# Overhead #############
            row = 4
            if sheet_name == 'Overhead':
                # Vehicle table
                sheet.merge_range('A4:C4', 'Vehicle', title_style)
                row += 1

                vehicle_headers = ['Task', 'Name', 'Qty']
                for col_num, header in enumerate(vehicle_headers):
                    sheet.write(row, col_num, header, header_style)
                row += 1

                vehicle_total_qty = 0.00

                for project in model:
                    for task in project.task_ids:
                        for req_vehcle_line_id in task.req_vehcle_line_ids:
                            for fleet_id in req_vehcle_line_id.fleet_ids:
                                sheet.write(row, 0, task.name, font_style)
                                sheet.write(row, 1, fleet_id.display_name, font_style)
                                sheet.write(row, 2, req_vehcle_line_id.hours, number_style)
                                
                                vehicle_total_qty += req_vehcle_line_id.hours
                                
                                row += 1

                # Write totals for equipments
                sheet.write(row, 1, 'Total', header_style)
                sheet.write(row, 2, vehicle_total_qty, total_style)
                
                row += 3

                # Equipments table
                sheet.merge_range('A{}:C{}'.format(row, row), 'Equipments', title_style)
                # sheet.merge_range('A10:C10', 'Equipments', title_style)
                row += 1

                equipment_headers = ['Task', 'Name', 'Qty']
                for col_num, header in enumerate(equipment_headers):
                    sheet.write(row, col_num, header, header_style)
                row += 1

                equipment_total_qty = 0.00  # Initialize total quantity for equipments

                for project in model:
                    for task in project.task_ids:
                        for req_equipment_line_id in task.req_equipment_line_ids:
                            for equipment_id in req_equipment_line_id.equipment_ids:
                                sheet.write(row, 0, task.name, font_style)
                                sheet.write(row, 1, equipment_id.display_name, font_style)
                                sheet.write(row, 2, req_equipment_line_id.hours, number_style)
                                
                                equipment_total_qty += req_equipment_line_id.hours  # Add to total quantity
                                
                                row += 1

                # Write totals for equipments
                sheet.write(row, 1, 'Total', header_style)
                sheet.write(row, 2, equipment_total_qty, total_style)
                
                row += 3

                sheet.merge_range('A{}:C{}'.format(row, row), 'Expenses', title_style)
                row += 1

                # Expense table
                expense_headers = ['Task', 'Category', 'Description', 'Total In Currency', 'Currency', 'Expense Date', 'Paid by', 'Employee', 'Company', 'Account']
                for col_num, header in enumerate(expense_headers):
                    sheet.write(row, col_num, header, header_style)
                row += 1

                total_expense = 0.00  # Initialize total expense

                for project in model:
                    for task in project.task_ids:
                        for expense_id in task.expense_ids:
                            sheet.write(row, 0, task.name, font_style)
                            sheet.write(row, 1, expense_id.product_id.display_name, font_style)
                            sheet.write(row, 2, expense_id.name, font_style)
                            sheet.write(row, 3, expense_id.total_amount, number_style)
                            sheet.write(row, 4, expense_id.currency_id.name, font_style)
                            sheet.write(row, 5, expense_id.date.strftime("%d-%m-%Y"), font_style)
                            sheet.write(row, 6, expense_id.payment_mode, font_style)
                            sheet.write(row, 7, expense_id.employee_id.display_name, font_style)
                            sheet.write(row, 8, expense_id.company_id.name, font_style)
                            sheet.write(row, 9, expense_id.account_id.display_name, font_style)
                            
                            total_expense += expense_id.total_amount  # Add to total expense
                            
                            row += 1

                # Write total for expenses
                sheet.write(row, 2, 'Total', header_style)
                sheet.write(row, 3, total_expense, total_style)

            ############# Bills #############
            row = 4
            if sheet_name == 'Bills':
                headers = ['Invoice Name', 'Vendor', 'Bill Date', 'Product', 'Account', 'Quantity', 'Uom', 'Unit Price', 'Taxes', 'Subtotal']
                for col_num, header in enumerate(headers):
                    sheet.write(row, col_num, header, header_style)
                row += 2
                bills_total_quantity = 0.00  # Initialize total subtotal
                bills_total_subtotal = 0.00  # Initialize total subtotal
                for project in model:
                    for task in project.task_ids:
                        bill_ids = request.env['account.move'].search([('task_id', '=', task.id)])
                        for bill_id in bill_ids:
                            for invoice_line_id in bill_id.invoice_line_ids:
                                sheet.write(row, 0, bill_id.name, font_style)
                                sheet.write(row, 1, bill_id.partner_id.display_name, font_style)
                                sheet.write(row, 2, bill_id.invoice_date.strftime("%d-%m-%Y"), font_style)
                                sheet.write(row, 3, invoice_line_id.product_id.name, font_style)
                                sheet.write(row, 4, invoice_line_id.account_id.display_name, font_style)
                                sheet.write(row, 5, invoice_line_id.quantity, number_style)
                                sheet.write(row, 6, invoice_line_id.product_uom_id.name, font_style)
                                sheet.write(row, 7, invoice_line_id.price_unit, number_style)
                                taxes = ', '.join([tax.name for tax in invoice_line_id.tax_ids])
                                sheet.write(row, 8, taxes, font_style)
                                sheet.write(row, 9, invoice_line_id.price_subtotal, number_style)
                                bills_total_subtotal += invoice_line_id.price_subtotal  # Add to total subtotal
                                bills_total_quantity += invoice_line_id.quantity
                                row += 1

                # Write total subtotal to the last row
                sheet.write(row, 0, 'Total', header_style)
                sheet.write(row, 5, bills_total_quantity, total_style)
                sheet.write(row, 9, bills_total_subtotal, total_style)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

        return response
