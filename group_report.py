import openpyxl
from openpyxl.utils import get_column_letter
import os
import dill as pkl

def make_group_report(date, directory="", pkl_file="groups.pkl"):
    with open(pkl_file, "rb") as f:
        groups = pkl.load(f)

    wb_name = os.path.join(directory, f"PIList-{date}.xlsx")

    font = openpyxl.styles.Font(name='Times New Roman')
    fontb = openpyxl.styles.Font(name='Times New Roman', bold=True)
    def add_cell(sheet, row, col, val, font=font):
        cell = sheet.cell(row=row, column=col)
        cell.value = val
        cell.font = font

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "PI info"

    add_cell(sheet, 1, 1, "gid", font=fontb)
    add_cell(sheet, 1, 2, "ngid", font=fontb)
    add_cell(sheet, 1, 3, "First name", font=fontb)
    add_cell(sheet, 1, 4, "Last name", font=fontb)
    add_cell(sheet, 1, 5, "Department", font=fontb)
    add_cell(sheet, 1, 6, "Email", font=fontb)
    for i in range(1, 7):
        sheet.column_dimensions[get_column_letter(i)].width = 20

    for n, group in groups.iterrows():
        n += 2
        gid = group[0]
        last_name = group[1]
        first_name = group[2]
        email = group[3]
        department = group[4]
        ngid = group[5]

        add_cell(sheet, n, 1, gid)
        add_cell(sheet, n, 2, ngid)
        add_cell(sheet, n, 3, first_name)
        add_cell(sheet, n, 4, last_name)
        add_cell(sheet, n, 5, department)
        add_cell(sheet, n, 6, email)

    wb.save(filename=wb_name)

if __name__ == "__main__":
    from datetime import date
    now = data.today()

    make_group_report(now.strftime('%b%Y'))
