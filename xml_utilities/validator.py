import os
import tkinter as tk
from tkinter import ttk
from dotenv import load_dotenv, find_dotenv
from utilities import main
from sqlalchemy import create_engine, select, text
import json
import pyodbc

load_dotenv(find_dotenv())


###### Set up gui theme and size ###########

db = os.environ["DB"]
server = os.environ["SERVER"]
tmp = open(os.environ["TABLES"])
imprt = open(os.environ["IMPORT"])

tmp_table = json.loads(tmp.read())
imp_table = json.loads(imprt.read())

# engine = create_engine('mssql+pyodbc://' + server + '/' + db + '?trusted_connection=yes&driver=SQL+Server+Native+Client+11.0')
conn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      f"Server={server};"
                      f"Database={db};"
                      "Trusted_Connection=yes;")
 
root = tk.Tk()

style = ttk.Style()

BG_COLOR = "#299617"
LBL_COLOR = "#D3D3D3"
TXT_COLOR = "#DCDCDC"
FONT = "Helvetica 12 bold"
TITLE = "XML Validator"
ICON = os.path.dirname(os.environ["ICON"])

w = 600
h = 400

root.resizable(False, False)

ws = root.winfo_screenwidth()
hs = root.winfo_screenheight()

root.iconbitmap(ICON)

x = (ws / 2) - (w / 2)
y = (hs / 2) - (h / 2)

root.title(TITLE)
root.geometry("%dx%d+%d+%d" % (w, h, x, y))
root.config(bg=BG_COLOR)

style.configure("TLabelframe", background=LBL_COLOR)
style.configure(
    "TLabelframe.Label", font=FONT, background=LBL_COLOR, color=BG_COLOR
)


if __name__ == "__main__":
    
    cursor = conn.cursor()
    
    # stmt = text('SELECT * FROM PiesImportHistory')
    # rows = conn.execute(stmt).fetchall()
    # print(rows)
    main(root,cursor, tmp_table,
         imp_table, LBL_COLOR, TXT_COLOR)
