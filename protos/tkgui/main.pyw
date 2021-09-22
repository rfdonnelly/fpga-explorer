#!/usr/bin/env python3

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import math

def to_hex(i, width=0):
    if i is None:
        return None
    else:
        return f"0x{i:x}"

class TreeNav(ttk.Treeview):
    def __init__(self, parent):
        columns=("offset", "size")
        super().__init__(parent, columns=columns)
        self.heading("#0", text="Name")
        self.heading("size", text="Size")
        self.heading("offset", text="Offset")

    def load_items(self, items):
        parent_id = ""
        to_visit = [(id, parent_id) for id in items["root"]["children"]]

        while len(to_visit) > 0:
            (id, parent_id) = to_visit.pop(0)
            name = id.split(".")[-1]
            item = items.get(id)
            if item is None:
                print(f"ERROR: Could not find item '{id}' in parent '{parent_id}'")
            values = (to_hex(item.get("offset")), to_hex(item.get("size")))
            self.insert(parent_id, "end", id, text=name, values=values, open=id.count(".") < 1)
            if item is not None:
                children = item.get("children")
                if children is not None:
                    for child_id in children:
                        to_visit.append((child_id, id))

    def item_full_name(self, item_id):
        full_name = self.item(item_id, "text")
        while self.parent(item_id) != "":
            item_id = self.parent(item_id)
            name = self.item(item_id, "text")
            full_name = f"{name}.{full_name}"
        return full_name

    def populate_demo_content(self):
        self.insert('', 'end', 'regs', text="regs", values=("0x0000", "0x1_0000"), open=TRUE)
        self.insert('regs', 'end', "regs.blk0", text="blk0", values=("0x0000", "0x0_1000"))
        self.insert('regs.blk0', 'end', text="reg0", values=("0x0", ""))
        self.insert('regs.blk0', 'end', text="reg1", values=("0x4", ""))
        self.insert('regs', 'end', "regs.blk1", text="blk1", values=("0x1000", "0x0_1000"))
        self.insert('regs.blk1', 'end', text="reg0", values=("0x0", ""))
        self.insert('regs.blk1', 'end', text="reg1", values=("0x4", ""))
        self.insert('regs', 'end', "regs.blk2", text="regs.blk2", values=("0x2000", "0x0_1000"))
        self.insert('regs.blk2', 'end', text="reg0", values=("0x0", ""))
        self.insert('regs.blk2', 'end', text="reg1", values=("0x4", ""))
        self.insert('', 'end', 'mems', text="mems", values=("0x10_0000", "0x2_0000"))

class FlatNav(ttk.Treeview):
    def __init__(self, parent):
        columns=("offset")
        super().__init__(parent, columns=columns)
        self.heading("#0", text="Name")
        self.heading("offset", text="Offset")

    def populate_demo_content(self):
        self.insert('', 'end', text="blk0.reg0", values=("0x0000"))
        self.insert('', 'end', text="blk0.reg1", values=("0x0004"))
        self.insert('', 'end', text="blk1.reg0", values=("0x1000"))
        self.insert('', 'end', text="blk1.reg1", values=("0x1004"))
        self.insert('', 'end', text="blk2.reg0", values=("0x2000"))
        self.insert('', 'end', text="blk2.reg1", values=("0x2004"))

class Menubar(Menu):
    def __init__(self, ui):
        super().__init__(ui.root)
        self.ui = ui
        self.root = ui.root
        self.root.option_add("*tearOff", FALSE)

        self.file_menu = Menu(self)
        self.help_menu = Menu(self)
        self.add_cascade(menu=self.file_menu, label="File")
        self.add_cascade(menu=self.help_menu, label="Help")
        self.file_menu.add_command(label="Connect...", command=self.do_connect)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Load Map...", command=filedialog.askopenfilename)
        self.file_menu.add_command(label="Load Script...", command=filedialog.askopenfilename)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.destroy, accelerator="Ctrl+W")
        self.help_menu.add_command(label="Help", command=self.do_nothing)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About", command=self.do_about)

        self.root.bind_all("<Control-w>", self.exit)

        self.root.config(menu=self)

    def do_connect(self):
        self.ui.statusbar["text"] = "Connected"

    def do_about(self):
        messagebox.showinfo(title="About", message="FPGA Explorer v0.1")

    def do_nothing(self):
        var = 0

    def exit(self, event):
        self.root.destroy()

class RegView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

    def unload_reg(self):
        for widget in self.grid_slaves():
            widget.destroy()

    def load_reg(self, reg):
        name = reg["name"]
        address = reg["address"]
        value = reg["value"]
        fields = reg["fields"]

        reg_width = 32

        label = ttk.Label(self, text=f"Name: {name}")
        label.grid(column=0, columnspan=16, row=0, sticky=(W, E))
        label = ttk.Label(self, text=f"Address: 0x{address:04x}", anchor="e")
        label.grid(column=16, columnspan=16, row=0, sticky=(W, E))

        for column in range(reg_width):
            index = reg_width - column - 1
            label = ttk.Label(self, text=index, borderwidth=1, relief="solid", anchor="center")
            if (column % 8 < 4):
                label.config(background="light gray")
            label.grid(column=column, row=1, sticky=(W, E))
            self.columnconfigure(column, weight=1)

        field_height = self.get_max_field_height(fields)
        for index, field in enumerate(fields):
            column = reg_width - (field["lsb"] + field["nbits"])
            columnspan = field["nbits"]
            # label = ttk.Label(self, text=field["name"], borderwidth=1, relief="solid", anchor="center")
            # label.grid(column=column, columnspan=columnspan, row=2, sticky=(W, E))
            # FIXME: Experiment to create a Canvas based label to enable text rotation
            label = FieldName(self, name=field["name"], nbits=field["nbits"], height=field_height)
            label.grid(column=column, columnspan=columnspan, row=2, sticky=(W, E))
            hex_digits = math.ceil(field["nbits"]/4)
            label = ttk.Label(self, text=f"0x{field['value']:0{hex_digits}x}", borderwidth=1, relief="solid", anchor="center", background="white")
            label.grid(column=column, columnspan=columnspan, row=3, sticky=(W, E))

        for row in range(5):
            self.rowconfigure(row, weight=1)

        label = ttk.Label(self, text=f"0x{value:08x}", borderwidth=1, relief="solid", anchor="center", background="white")
        label.grid(column=0, columnspan=32, row=4, sticky=(W, E))

    def get_max_field_height(self, fields):
        return max([self.get_field_height(field) for field in fields])

    def get_field_height(self, field):
        len_name = len(field["name"])
        rotate = len_name > 2*field["nbits"]

        if (rotate):
            return len_name * 7
        else:
            return 15

# Use a canvas instead of a label to allow text rotation
class FieldName(ttk.Frame):
    def __init__(self, parent, name="null", nbits=1, height=1):
        super().__init__(parent, borderwidth=1, relief="solid")

        width = 0
        angle = 0
        rotate = len(name) > 2*nbits

        if (rotate):
            width = 15
            angle = 90
        else:
            width = len(name) * 10
            angle = 0

        self.canvas = Canvas(self, height=height, width=width)
        self.canvas.grid(column=0, row=0, sticky=(W, E))
        self.columnconfigure(0, weight=1)
        self.canvas.bind("<Configure>", self.on_resize)
        self.text = self.canvas.create_text(self.canvas.winfo_width()/2, 10, text=name, anchor="center", angle=angle)

    def on_resize(self, event):
        self.canvas.coords(self.text, event.width/2, event.height/2)

class GUI:
    def __init__(self):
        self.docked = 1

        self.root = Tk()
        self.root.title("FPGA Explorer")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        menu = Menubar(self)

        self.statusbar = ttk.Label(self.root, text="Not connected", anchor=E)
        self.statusbar.pack(side=BOTTOM, fill=X)
        menu.statusbar = self.statusbar

        self.split_v = ttk.Panedwindow(self.root, orient=VERTICAL, height=600)
        self.split_v.pack(fill=BOTH, expand=TRUE)
        self.top = ttk.Frame(self.split_v)
        self.top.pack(fill=BOTH, expand=TRUE)
        self.bottom = ttk.Frame(self.split_v)
        self.bottom.pack(fill=BOTH, expand=TRUE)
        # FIXME: weights aren't working as expected for some reason, they seem
        # to be ignored here. Maybe the children need to be Frames? Sizing
        # seems to be dictated by children.
        self.split_v.add(self.top, weight=4)
        self.split_v.add(self.bottom, weight=1)

        self.console = Text(self.bottom, height=10)
        self.console.pack(fill=BOTH, expand=TRUE)
        self.console.insert("1.0", "FPGA Explorer v0.1\n")
        self.console.insert("2.0", "Type \"help\" for more information.\n")
        self.show_prompt()
        self.console.bind("<Key-Return>", self.console_enter_callback)
        self.console.focus_force()

        self.split_h = ttk.Panedwindow(self.top, orient=HORIZONTAL)
        self.split_h.pack(fill=BOTH, expand=TRUE)
        self.left = ttk.Frame(self.split_h)
        self.left.pack(fill=BOTH, expand=TRUE)
        self.right = Frame(self.split_h)
        self.right.pack(fill=BOTH, expand=TRUE)
        self.split_h.add(self.left, weight=1)
        self.split_h.add(self.right, weight=2)

        self.treenav = TreeNav(self.left)
        self.treenav.pack(fill=BOTH, expand=TRUE)
        # self.treenav.populate_demo_content()
        self.treenav.bind("<<TreeviewSelect>>", self.treenav_select_callback)

        # self.flatnav = FlatNav(self.left)
        # self.flatnav.grid(column=0, row=1, sticky=(N, S, W, E))
        # self.flatnav.populate_demo_content()

        self.items = {
            "root": {
                "type": "root",
                "children": [
                    "regs",
                    "mems",
                ],
            },
            "regs": {
                "type": "block",
                "offset": 0x0,
                "children": [
                    "regs.blk0",
                    "regs.blk1",
                    "regs.blk2",
                ],
            },
            "mems": {
                "type": "block",
                "offset": 0x200000,
                "size": 0x20000,
                "children": [
                    "mems.tx",
                    "mems.rx",
                ],
            },
            "regs.blk0": {
                "type": "block",
                "offset": 0x0000,
                "size": 0x1000,
                "children": [
                    "regs.blk0.reg0",
                    "regs.blk0.reg1",
                ],
            },
            "regs.blk1": {
                "type": "block",
                "offset": 0x1000,
                "size": 0x1000,
                "children": [
                    "regs.blk1.reg0",
                    "regs.blk1.reg1",
                ],
            },
            "regs.blk2": {
                "type": "block",
                "offset": 0x2000,
                "size": 0x1000,
                "children": [
                    # "regs.blk2.reg0",
                    # "regs.blk2.reg1",
                ],
            },
            "mems.tx": {
                "type": "mem",
                "offset": 0x0000,
                "size": 0x10000,
            },
            "mems.rx": {
                "type": "mem",
                "offset": 0x0000,
                "size": 0x10000,
            },
            "regs.blk0.reg0": {
                "type": "reg",
                "name": "regs.blk0.reg0",
                "address": 0x0,
                "value": 0x600dc0de,
                "fields": [
                    {
                        "name": "f4",
                        "nbits": 4,
                        "lsb": 28,
                        "value": 0x6,
                    }, {
                        "name": "rsvd1",
                        "nbits": 8,
                        "lsb": 20,
                        "value": 0x00,
                    }, {
                        "name": "f3",
                        "nbits": 8,
                        "lsb": 12,
                        "value": 0xdc,
                    }, {
                        "name": "rsvd0",
                        "nbits": 4,
                        "lsb": 8,
                        "value": 0x0,
                    }, {
                        "name": "f1",
                        "nbits": 4,
                        "lsb": 4,
                        "value": 0xd,
                    }, {
                        "name": "long_field_name",
                        "nbits": 4,
                        "lsb": 0,
                        "value": 0xe,
                    },
                ],
            },
            "regs.blk0.reg1": {
                "type": "reg",
                "name": "regs.blk0.reg1",
                "address": 0x4,
                "value": 0x0000000,
                "fields": [
                    {
                        "name": "f3",
                        "nbits": 8,
                        "lsb": 24,
                        "value": 0x00,
                    }, {
                        "name": "f2",
                        "nbits": 8,
                        "lsb": 16,
                        "value": 0x00,
                    }, {
                        "name": "f1",
                        "nbits": 8,
                        "lsb": 8,
                        "value": 0x00,
                    }, {
                        "name": "f0",
                        "nbits": 8,
                        "lsb": 0,
                        "value": 0xDC,
                    },
                ],
            },
            "regs.blk1.reg0": {
                "type": "reg",
                "name": "regs.blk1.reg0",
                "address": 0x1000,
                "value": 0x0badf00d,
                "fields": [
                    {
                        "name": "address",
                        "nbits": 32,
                        "lsb": 0,
                        "value": 0x0badf00d,
                    },
                ],
            },
            "regs.blk1.reg1": {
                "type": "reg",
                "name": "regs.blk1.reg1",
                "address": 0x1004,
                "value": 0x600dc0de,
                "fields": [
                    {
                        "name": "f4",
                        "nbits": 4,
                        "lsb": 28,
                        "value": 0x6,
                    }, {
                        "name": "rsvd1",
                        "nbits": 8,
                        "lsb": 20,
                        "value": 0x00,
                    }, {
                        "name": "f3",
                        "nbits": 8,
                        "lsb": 12,
                        "value": 0xDC,
                    }, {
                        "name": "rsvd0",
                        "nbits": 4,
                        "lsb": 8,
                        "value": 0x0,
                    }, {
                        "name": "f1",
                        "nbits": 4,
                        "lsb": 4,
                        "value": 0xD,
                    }, {
                        "name": "long_field_name",
                        "nbits": 4,
                        "lsb": 0,
                        "value": 0xE,
                    },
                ],
            },
        }

        self.regview = RegView(self.right)
        self.regview.pack(side=TOP, fill=X, padx=(0, 5))

        self.treenav.load_items(self.items)
        self.treenav.see("regs.blk0.reg0")
        self.treenav.selection_set("regs.blk0.reg0")
        self.regview.load_reg(self.items.get("regs.blk0.reg0"))

        # self.regview = ttk.Frame(self.split_h)

        self.root.bind("<Control-d>", self.toggle_dock)
        import pathlib
        ico_path = pathlib.Path(__file__).parent.resolve().joinpath("chip.ico")
        try:
            self.root.iconbitmap(ico_path)
        except:
            print(f"warning: resource not found at path '{ico_path}'")
            pass

        # Set the split sash position
        #
        # First we need to update for the initial layout, then we can set the
        # sash position.  If we don't update, an update will be performed
        # automatically after setting the sash position and overwrite it.
        self.root.update()
        self.split_h.sashpos(0, 400)

        # self.treenav.focus()

    def show_prompt(self):
        self.console_write(">>> ")
        self.console.mark_set("iomark", "insert")
        self.console.mark_gravity("iomark", "left")

    def console_write(self, s):
        self.console.insert("insert", s)
        self.console.see("insert")
        # self.console.update()

    def console_enter_callback(self, event):
        line = self.console.get("iomark", "end-1c")
        self.console_write("\n")
        if line == "help":
            import inspect
            self.console_write(inspect.cleandoc("""
                Available commands:

                * write(<reg|offset>, <data>) -- Write a named register or offset.
                * read(<reg|offset>) -- Read a named register or offset.
            """))
            self.console_write("\n")
        elif line == "quit":
            self.root.destroy()
            return
        else:
            try:
                result = eval(line)
                if result:
                    self.console_write(result)
                self.console_write("\n")
            except:
                self.console_write("Unrecognized command\n")
                pass

        self.show_prompt()
        return "break"

    def treenav_select_callback(self, event):
        item_id = self.treenav.focus()
        item = self.treenav.item(item_id)
        item_full_name = self.treenav.item_full_name(item_id)
        parent_id = self.treenav.parent(item_id)
        parent = self.treenav.item(parent_id)

        reg = self.items.get(item_full_name)
        if reg is not None and reg.get("type") == "reg":
            self.regview.unload_reg()
            self.regview.load_reg(reg)
            self.console_write(f"read({reg['name']})\n")
            self.console_write(f"0x{reg['value']:08x}\n")
            self.show_prompt()

    def toggle_dock(self, event):
        if (self.docked):
            self.root.wm_manage(self.right)
        else:
            self.root.wm_forget(self.right)
            self.right.pack(fill=BOTH, expand=TRUE)
            self.split_h.add(self.right)

        self.docked ^= 1

    def run(self):
        self.root.mainloop()

GUI().run()
