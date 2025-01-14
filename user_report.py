import openpyxl
import dill as pkl
import os
from openpyxl.utils import get_column_letter


def make_user_report(date, directory, pkl_file):
    with open(pkl_file, "rb") as f:
        users = pkl.load(f)

    wb_name = os.path.join(directory, f"UserList-{date}.xlsx")

    font = openpyxl.styles.Font(name='Times New Roman')
    fontb = openpyxl.styles.Font(name='Times New Roman', bold=True)

    def add_cell(sheet, row, col, val, font=font):
        cell = sheet.cell(row=row, column=col)
        cell.value = val
        cell.font = font

    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "User info"

    add_cell(sheet, 1, 1, "uid", font=fontb)
    add_cell(sheet, 1, 2, "gid", font=fontb)
    add_cell(sheet, 1, 3, "nuid", font=fontb)
    add_cell(sheet, 1, 4, "First name", font=fontb)
    add_cell(sheet, 1, 5, "Last name", font=fontb)
    add_cell(sheet, 1, 6, "Email", font=fontb)
    for i in range(1, 7):
        sheet.column_dimensions[get_column_letter(i)].width = 20

    for n, user in users.iterrows():
        n += 2
        uid = user[0]
        gid = user[1]
        nuid = user[2]
        first_name = user[3]
        last_name = user[4]
        email = user[5]

        add_cell(sheet, n, 1, uid)
        add_cell(sheet, n, 2, gid)
        add_cell(sheet, n, 3, nuid)
        add_cell(sheet, n, 4, first_name)
        add_cell(sheet, n, 5, last_name)
        add_cell(sheet, n, 6, email)

    wb.save(filename=wb_name)


if __name__ == "__main__":
    from datetime import date
    now = date.today()

    data_path = os.getenv("REPORT_DATA_PATH", os.getcwd())
    users_filename = os.path.join(data_path, "users.pkl")

    make_user_report(now.strftime('%b%Y'), directory=os.getcwd(), pkl_file=users_filename)
