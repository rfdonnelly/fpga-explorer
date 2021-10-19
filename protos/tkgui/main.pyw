#!/usr/bin/env python3

CEF = True

if CEF:
    from cefpython3 import cefpython as cef # type: ignore

import math

from pathlib import Path
import platform
import random

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from typing import List
from typing import Optional
from typing import Tuple

# Platforms
WINDOWS = (platform.system() == "Windows")
LINUX = (platform.system() == "Linux")
MAC = (platform.system() == "Darwin")

def to_hex(value: Optional[int], nbits: int = 0) -> str:
    digits = math.ceil(nbits/4)

    if value is None:
        return "?" * max(1, digits)

    if nbits > 0:
        return f"0x{value:0{digits}x}"
    else:
        return f"0x{value:x}"

def to_bin(value: Optional[int], nbits: int = 0) -> str:
    if value is None:
        return "?" * max(1, nbits)

    if nbits > 0:
        return f"0b{value:032b}"
    else:
        return f"0b{value}:b"

def parse_int(value, base):
    try:
        return int(value, base)
    except:
        return None

def reg_to_field(reg_value: Optional[int], field_lsb: int, field_nbits: int) -> Optional[int]:
    if reg_value is None:
        return None

    mask = (1 << field_nbits) - 1
    return (reg_value >> field_lsb) & mask

def field_to_reg(field_value: Optional[int], field_lsb: int, field_nbits: int) -> Optional[int]:
    if field_value is None:
        return None

    field_mask = (1 << field_nbits) - 1
    return (field_value & field_mask) << field_lsb

class ConnectorInterface:
    """The interface for connecting to a target device.

    Used to implement connectors for various interaces (e.g. UART, JTAG, etc.)
    """

    def available_ports(self) -> List[str]:
        """Returns a list of available ports to connect to."""
        pass

    def connect(self, port: Optional[str]) -> Optional[str]:
        """Connects to a port.

        If no port is provided, attempt to connect to the first available port.
        If no ports are available, return an error message.

        On success, returns None.
        On failure, returns an error message.
        """
        pass

    def is_connected(self) -> bool:
        """Returns the connection status."""
        pass

    def read(self, addr: int) -> Tuple[Optional[int], Optional[str]]:
        """Reads an address.

        Assumes a 32-bit address and a 32-bit data word.

        On success, returns a tuple containing the data and None.
        On failure, returns a tuple containing None and an error message.
        """
        pass

    def write(self, addr: int, data: int) -> Optional[str]:
        """Write an address.

        Assumes a 32-bit address and a 32-bit data word.

        On success, returns None.
        On failure, returns an error message.
        """
        pass

class VirtualConnector(ConnectorInterface):
    """A connecter that allows demoing Register Explorer w/o having to connect to actual hardware.

    It implements a read/write memory model.  Address locations are initialized on read (if not previously initialized) to a random value.
    """

    def __init__(self):
        self.memory = {}

    def get(self, addr: int) -> int:
        if self.memory.get(addr) is None:
            self.set(addr, random.getrandbits(32))

        return self.memory[addr]

    def set(self, addr: int, data: int) -> None:
        self.memory[addr] = data

    def available_ports(self) -> List[str]:
        """Returns a list of available ports to connect to."""
        return ["Virtual"]

    def connect(self, port: Optional[str]) -> Optional[str]:
        """Connects to a port.

        If no port is provided, attempt to connect to the first available port.
        If no ports are available, return an error message.

        On success, returns None.
        On failure, returns an error message.
        """
        return None

    def is_connected(self) -> bool:
        """Returns the connection status."""
        return True

    def read(self, addr: int) -> Tuple[Optional[int], Optional[str]]:
        """Reads an address.

        Assumes a 32-bit address and a 32-bit data word.

        On success, returns a tuple containing the data and None.
        On failure, returns a tuple containing None and an error message.
        """
        return (self.get(addr), None)

    def write(self, addr: int, data: int) -> Optional[str]:
        """Writes an address.

        Assumes a 32-bit address and a 32-bit data word.

        On success, returns None.
        On failure, returns an error message.
        """
        self.set(addr, data)

        return None

connecter = VirtualConnector()

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
        self.ui.status["text"] = "Connected"

    def do_about(self):
        messagebox.showinfo(title="About", message="Register Explorer v0.1")

    def do_nothing(self):
        var = 0

    def exit(self, event):
        self.root.destroy()

class StringVarEx(StringVar):
    """Adds a write callback and provides a silent set function that bypasses the callback."""
    def __init__(self, parent, text, name, callback):
        super().__init__(parent, text, name)

        self.callback = callback
        self.trace_id = self.trace_add("write", self.callback)

    def silent_set(self, s):
        self.trace_vdelete("w", self.trace_id)
        self.set(s)
        self.trace_id = self.trace_add("write", self.callback)

class RegView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.reg_svar = StringVarEx(self, "????????", "reg_svar", self.reg_svar_write_callback)

        self.layout = RegLayout(self, self.reg_svar)
        self.layout.pack(side=TOP, fill=X, pady=(0, 5))

        self.buttons = ttk.Frame(self)
        self.buttons.pack(side=TOP, fill=X, pady=(0, 5))
        self.read_button = ttk.Button(self.buttons, text="r", width=2, command=self.read_callback)
        self.read_button.pack(side=RIGHT, fill=Y)
        self.write_button = ttk.Button(self.buttons, text="w", width=2, command=self.write_callback)
        self.write_button.pack(side=RIGHT, fill=Y)
        self.sep = ttk.Frame(self.buttons, width=10)
        self.sep.pack(side=RIGHT, fill=Y)
        self.to_hex_button = ttk.Button(self.buttons, text="🡒h", width=3, command=self.to_hex_callback)
        self.to_hex_button.pack(side=RIGHT, fill=Y)
        self.to_bin_button = ttk.Button(self.buttons, text="🡒b", width=3, command=self.to_bin_callback)
        self.to_bin_button.pack(side=RIGHT, fill=Y)
        self.to_dec_button = ttk.Button(self.buttons, text="🡒d", width=3, command=self.to_dec_callback)
        self.to_dec_button.pack(side=RIGHT, fill=Y)

        self.fieldtable = RegFieldTable(self)
        self.fieldtable.pack(side=TOP, fill=X)

    def write_callback(self):
        write_value = parse_int(self.layout.value.get(), 0)
        addr = self.reg["address"]
        connecter.write(addr, write_value)
        read_value = connecter.read(addr)
        self.update_value(read_value)

    def read_callback(self):
        addr = self.reg["address"]
        read_value = connecter.read(addr)
        self.update_value(read_value)

    def to_bin_callback(self):
        value = parse_int(self.reg_svar.get(), 0)
        self.reg_svar.set(to_bin(value, 32))

    def to_hex_callback(self):
        value = parse_int(self.reg_svar.get(), 0)
        self.reg_svar.set(to_hex(value, 32))

    def to_dec_callback(self):
        value = parse_int(self.reg_svar.get(), 0)
        self.reg_svar.set(f"{value}")

    def reg_svar_write_callback(self, *args):
        value = parse_int(self.reg_svar.get(), 0)
        self.layout.update_value(self.reg, value)

    def update_value(self, value):
        self.reg_svar.set(to_hex(value, 32))
        self.layout.update_value(self.reg, value)

    def load_reg(self, reg):
        self.reg = reg
        self.layout.load_reg(reg)
        self.fieldtable.load_fields(reg["fields"])

class RegFieldTable(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.bind("<Configure>", self.on_resize)
        self.table_texts = []

    def unload_fields(self):
        for widget in self.grid_slaves():
            widget.destroy()
        self.table_texts = []

    def load_fields(self, fields):
        self.unload_fields()

        headings = ["Bits", "Name", "Access", "Description"]
        weights = [1, 2, 1, 10]
        for column, heading in enumerate(headings):
            label = ttk.Label(self, text=heading, borderwidth=1, relief="solid", padding=5)
            label.grid(column=column, row=0, sticky=(W, E))
            label.config(background="light gray")
            self.columnconfigure(column, weight=weights[column])

        for field_index, field in enumerate(fields):
            lsb = field["lsb"]
            msb = lsb + field["nbits"] - 1
            bits = lsb if msb == lsb else f"{msb}:{lsb}"
            cells = [bits, field["name"], field["access"], field.get("doc") or ""]
            widths = [5, 25, 7, 50]
            row = field_index + 1
            row_texts = {}
            for column, cell in enumerate(cells):
                text = Text(self, height=1, width=widths[column], wrap="word")
                text.grid(column=column, row=row, sticky=(W, E))
                text.insert("1.0", cell)
                row_texts[headings[column]] = text
                text["state"] = "disabled"
                if headings[column] == "Description":
                    text.configure(font=("TkDefaultFont", 10, ""))
            self.table_texts.append(row_texts)


    def on_resize(self, event):
        # Resize each row based on the number of description display lines
        for row_texts in self.table_texts:
            text = row_texts["Description"]
            lines = text.count("1.0", "end", "displaylines")
            for text in row_texts.values():
                text["height"] = lines

class RegLayout(ttk.Frame):
    def __init__(self, parent, reg_svar):
        super().__init__(parent)
        self.reg_svar = reg_svar
        self.init()

    def init(self):
        for widget in self.grid_slaves():
            widget.destroy()

        self.field_svars = {}
        self.field_entries = {}

    def load_reg(self, reg):
        self.init()

        name = reg["name"]
        address = reg["address"]
        reg_value = connecter.read(address)
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
            field_name = field["name"]

            column = reg_width - (field["lsb"] + field["nbits"])
            columnspan = field["nbits"]
            label = FieldName(self, name=field_name, nbits=field["nbits"], height=field_height)
            label.grid(column=column, columnspan=columnspan, row=2, sticky=(W, E))
            field_svar = StringVarEx(self, "?", field_name, lambda *_, reg=reg, field_name=field_name: self.field_svar_write_callback(reg, field_name))
            self.field_svars[field_name] = field_svar
            label = Entry(self, justify="center", textvariable=field_svar)
            label.grid(column=column, columnspan=columnspan, row=3, sticky=(W, E))
            self.field_entries[field_name] = label

        for row in range(5):
            self.rowconfigure(row, weight=1)

        self.value = Entry(self, justify="center", textvariable=self.reg_svar)
        self.reg_svar.set("????????")
        self.value.grid(column=0, columnspan=32, row=4, sticky=(W, E))

    def update_value(self, reg, value):
        fields = reg["fields"]
        for field in fields:
            field_name = field["name"]
            field_value = reg_to_field(value, field["lsb"], field["nbits"])
            self.field_svars[field_name].silent_set(to_hex(field_value, field["nbits"]))

    def field_svar_write_callback(self, reg, field_name):
        field_entry = self.field_entries.get(field_name)
        if field_entry is not None:
            field_entry["background"] = "light yellow"
            self.value["background"] = "light yellow"

        value = 0
        for field in reg["fields"]:
            field_name = field["name"]
            field_value = parse_int(self.field_svars[field_name].get(), 0)
            value |= field_to_reg(field_value, field["lsb"], field["nbits"])

        self.reg_svar.silent_set(to_hex(value, 32))

    def get_max_field_height(self, fields):
        return max([self.get_field_height(field) for field in fields])

    def get_field_height(self, field):
        len_name = len(field["name"])
        rotate = len_name > 2*field["nbits"]

        if (rotate):
            return len_name * 10
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
        font = ("Courier New", 10, "")
        self.text = self.canvas.create_text(self.canvas.winfo_width()/2, 10, text=name, anchor="center", angle=angle, font=font)

    def on_resize(self, event):
        self.canvas.coords(self.text, event.width/2, event.height/2)

class CEFRegView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        self.browser = None

        super().__init__(parent, *args, **kwargs)

        settings = {}
        if MAC:
            settings["external_message_pump"] = True
        cef.Initialize(settings=settings)

        self.bind("<Configure>", self.on_configure)

    def embed_browser(self):
        window_info = cef.WindowInfo()
        rect = [0, 0, self.winfo_width(), self.winfo_height()]
        window_info.SetAsChild(self.get_window_handle(), rect)

        file_path = Path(__file__).parent.parent.joinpath("web/index.html").absolute()
        file_uri = f"file://{file_path}"
        self.browser = cef.CreateBrowserSync(window_info, url=file_uri)
        assert self.browser

        bindings = cef.JavascriptBindings()
        bindings.SetFunction("py_read", self.py_read)
        bindings.SetFunction("py_write", self.py_write)
        self.browser.SetJavascriptBindings(bindings)

        self.message_loop_work()

    def get_window_handle(self):
        if MAC:
            # Do not use self.winfo_id() on Mac, because of these issues:
            # 1. Window id sometimes has an invalid negative value (Issue #308).
            # 2. Even with valid window id it crashes during the call to NSView.setAutoresizingMask:
            #    https://github.com/cztomczak/cefpython/issues/309#issuecomment-661094466
            #
            # To fix it using PyObjC package to obtain window handle. If you change structure of windows then you
            # need to do modifications here as well.
            #
            # There is still one issue with this solution. Sometimes there is more than one window, for example when application
            # didn't close cleanly last time Python displays an NSAlert window asking whether to Reopen that window. In such
            # case app will crash and you will see in console:
            # > Fatal Python error: PyEval_RestoreThread: NULL tstate
            # > zsh: abort      python tkinter_.py
            # Error messages related to this: https://github.com/cztomczak/cefpython/issues/441
            #
            # There is yet another issue that might be related as well:
            # https://github.com/cztomczak/cefpython/issues/583

            # noinspection PyUnresolvedReferences
            from AppKit import NSApp # type: ignore
            # noinspection PyUnresolvedReferences
            import objc # type: ignore
            logger.info("winfo_id={}".format(self.winfo_id()))
            # noinspection PyUnresolvedReferences
            content_view = objc.pyobjc_id(NSApp.windows()[-1].contentView())
            logger.info("content_view={}".format(content_view))
            return content_view
        elif self.winfo_id() > 0:
            return self.winfo_id()
        else:
            raise Exception("Couldn't obtain window handle")

    def message_loop_work(self):
        cef.MessageLoopWork()
        self.after(10, self.message_loop_work)

    def on_configure(self, event):
        if not self.browser:
            self.embed_browser()

        if WINDOWS:
            ctypes.windll.user32.SetWindowPos(
                self.browser.GetWindowHandle(), 0,
                0, 0, event.width, event.height, 0x0002)
        elif LINUX:
            self.browser.SetBounds(0, 0, event.width, event.height)

        self.browser.NotifyMoveOrResizeStarted()    

    def load_reg(self, reg):
        # FIXME: We don't create the browser until first resize event, and we
        # attempt to load_reg before the first resize (before the browser has
        # been created). So fix by making this conditional for now.
        if self.browser:
            self.browser.ExecuteFunction("load_reg", reg)

    def py_read(self, addr, callback):
        data = connecter.read(addr)
        callback.Call(data)

    def py_write(self, addr, data):
        connecter.write(addr, parse_int(data, 0))

class GUI:
    def __init__(self):
        self.docked = 1

        self.root = Tk()
        self.root.title("Register Explorer")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        menu = Menubar(self)

        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(side=BOTTOM, fill=X)
        self.sizegrip = ttk.Sizegrip(self.statusbar)
        self.sizegrip.pack(side=RIGHT)
        self.status = ttk.Label(self.statusbar, text="Not connected", anchor=E)
        self.status.pack(side=RIGHT, fill=X)

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
        self.console.insert("1.0", "Register Explorer v0.1\n")
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
                "size": 0x10000,
                "children": [
                    "regs.nand0",
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
            "regs.nand0": {
                "type": "block",
                "offset": 0x0,
                "size": 0x1000,
                "children": [
                    "regs.nand0.rev",
                    "regs.nand0.id",
                    "regs.nand0.cmd",
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
            "regs.nand0.rev": {
                "type": "reg",
                "name": "regs.nand0.rev",
                "offset": 0x0,
                "size": 0x4,
                "address": 0x0,
                "value": 0x600dc0de,
                "fields": [
                    {
                        "name": "rsvd0",
                        "nbits": 8,
                        "lsb": 24,
                        "access": "ro",
                        "doc": "Reserved."
                    }, {
                        "name": "major",
                        "nbits": 8,
                        "lsb": 16,
                        "access": "ro",
                        "doc": "Major component of the version number. A change to the major component communicates a breaking change.",
                    }, {
                        "name": "minor",
                        "nbits": 8,
                        "lsb": 8,
                        "access": "ro",
                        "doc": "Minor component of the version number. A change to the minor component communicates a non-breaking change that adds functionality.",
                    }, {
                        "name": "patch",
                        "nbits": 8,
                        "lsb": 0,
                        "access": "ro",
                        "doc": "Patch component of the version number. A change to the patch component communicates a bug fix.",
                    }
                ],
            },
            "regs.nand0.id": {
                "type": "reg",
                "name": "regs.nand0.id",
                "offset": 0x4,
                "size": 0x4,
                "address": 0x4,
                "value": 0x600dc0de,
                "fields": [
                    {
                        "name": "rsvd0",
                        "nbits": 28,
                        "lsb": 4,
                        "access": "ro",
                        "doc": "Reserved."
                    }, {
                        "name": "bankid",
                        "nbits": 4,
                        "lsb": 0,
                        "access": "ro",
                        "doc": """The lowest 4 bits of the bank_id input port.
* 0xA -- NAND sequencer 0
* 0xB -- NAND sequencer 1""",
                    }
                ],
            },
            "regs.nand0.cmd": {
                "type": "reg",
                "name": "regs.nand0.cmd",
                "offset": 0x8,
                "size": 0x4,
                "address": 0x8,
                "value": 0x600dc0de,
                "fields": [
                    {
                        "name": "cmd",
                        "nbits": 8,
                        "lsb": 24,
                        "access": "rw",
                        "doc": """On write:

* 0x40 -- Issue a NOP command
* 0xFF -- Issue a RESET command
* 0x90 -- Issue a READ_ID command
* 0xE1 -- Issue a READ_ID_ANY
* 0x43 -- Issue a SET_TIMING_MODE
* 0x44 -- Issue a GET_TIMING_MODE
* 0x41 -- Issue a SET_TIMING_MODE_SGL_LUN
* 0x42 -- Issue a GET_TIMING_MODE_EUR
* 0x70 -- Issue a READ_STAT (read status)
* 0x48 -- Issue a ENA_ECC
* 0x55 -- Issue a DIS_ECC
* 0x50 -- Issue a START_DATA_CHECK
* 0x52 -- Issue a STOP_DATA_CHECK
* 0x53 -- Issue a CHECK_DDR_DATA
* 0x97 -- Issue a SET_EXT_WP (set external/global write protect)
* 0x98 -- Issue a CLR_EXT_WP (clears external/global write protect)
* 0x99 -- Issue a SET_INT_WP (sets internal per-LUN write protect)
* 0x9A -- Issue a CLR_INT_WP (clears internal per-LUN write protect)
* 0x9B -- Issue a CLR_LUN_ERR (clears all error bits for selected LUN)
* 0x9D -- Issue a CLR_ECC_ERR (clears ECC error counters in register NANDERRCNT)
* 0x9E -- Issue a CLR_RESP (clears NANDRESP0/1 registers)
* 0x49 -- Issue a ENA_TMO (re-enables timeout)
* 0x56 -- Issue a DIS_TMO (disables timeout)
* 0xBA -- Issue a BATCH_CMD = starts a batch command session (stored in SDRAM/DDR)
* 0x46 -- Issue a SET_CFG_SPARE_PGSZ (sets the page spare size if default not acceptable)
* 0x47 -- Issue a GET_CFG (reads Eureka configuration register for spare page size and other settings)
* 0x33 -- Issue a READ_CUSTOM_EUR (reads Eureka controller register)
* 0x36 -- Issue a WRITE_CUSTOM_EUR (writes to Eureka controller register)

On read: last command.

IMPORTANT NOTE: Before writing a new command to this register, VCESW must first ensure that the NAND sequencer is ready to accept new commands (by polling register NANDGLBSTAT until bit nand_seq_rdy high)""",
                    }, {
                        "name": "arg",
                        "nbits": 8,
                        "lsb": 16,
                        "access": "rw",
                        "doc": "Command argument for direct commands.",
                    }, {
                        "name": "lunid",
                        "nbits": 4,
                        "lsb": 12,
                        "access": "rw",
                        "doc": """The target LUN ID for the command.

* 0x0 - 0x7 -- Select single specified LUN (8 LUNs per NAND sequencer)
* 0xF -- Broadcast to all 8 LUNs
* 0x8 - 0xE -- Equivalent to 0x0 - 0x7 respectively.""",
                    }, {
                        "name": "ignore_descr_cs",
                        "nbits": 1,
                        "lsb": 11,
                        "access": "rw",
                        "doc": "Ignore descriptor checksum violation(s) and proceed with batch command(s) regardless. Nominally low.",
                    }, {
                        "name": "rsvd0",
                        "nbits": 2,
                        "lsb": 9,
                        "access": "ro",
                        "doc": "Reserved.",
                    }, {
                        "name": "done_irq_mode",
                        "nbits": 1,
                        "lsb": 8,
                        "access": "rw",
                        "doc": """Select the mode for the DONE_IRQ:

* 0 -- DONE_IRQ will fine upon command completion for any command (batch and direct commands)
* 1 -- DONE_IRQ will only fire upon batch command completion""",
                    }, {
                        "name": "tmo_sel",
                        "nbits": 2,
                        "lsb": 6,
                        "access": "rw",
                        "doc": """Select the timeout value.

* 0x0 -- Timeout after 4ms (exactly 3.93ms)
* 0x1 -- Timeout after 8ms (exactly 7.86ms)
* 0x2 -- Timeout after 32ms (exactly 31.46ms)
* 0x3 -- Timeout after 4ms (exactly 3.93ms)""",
                    }, {
                        "name": "continue_on_abort_fail",
                        "nbits": 6,
                        "lsb": 0,
                        "access": "rw",
                        "doc": """Set high individual bits if you want the design to continue to the next command in the batch upon encountering abort or other failure condition. Design will not execute the command resulting in the abort/failure condition but will resume normal execution by skipping to the next command in the batch. Each bit controls continue/terminate for 1 condition.

* Bit 5 -- Continue on page-erased-verify failure (some page data non-FFs)
* Bit 4 -- Continue on DBE on READ command
* Bit 3 -- Continue on program/erase failure (e.g. on access to a bad block)
* Bit 2 -- Continue on write protect violation (abort_id 0xB)
* Bit 1 -- Continue on timeout (fail_id 0x1)
* Bit 0 -- Continue on bad descriptor (abort_ids 0x3-0xA)

If all bits low, the design will stop upon any abort/failure condition described above and will not execute any of the following commands scheduled in the batch. Regardless of bits set in this field, the design will never continue upon abort conditions 0x1, 0x2 (illegal command in NANDCMDR.nand_cmd or 0 in NANDNCMDS.nand_ncmds).""",
                    }
                ],
            },
            "regs.blk0.reg0": {
                "type": "reg",
                "name": "regs.blk0.reg0",
                "offset": 0x0,
                "size": 0x4,
                "address": 0x0,
                "value": 0x600dc0de,
                "fields": [
                    {
                        "name": "f4",
                        "nbits": 4,
                        "lsb": 28,
                        "access": "rw",
                    }, {
                        "name": "rsvd1",
                        "nbits": 8,
                        "lsb": 20,
                        "access": "ro",
                    }, {
                        "name": "f3",
                        "nbits": 8,
                        "lsb": 12,
                        "access": "rw",
                    }, {
                        "name": "rsvd0",
                        "nbits": 4,
                        "lsb": 8,
                        "access": "ro",
                    }, {
                        "name": "f1",
                        "nbits": 4,
                        "lsb": 4,
                        "access": "rw",
                    }, {
                        "name": "long_field_name",
                        "nbits": 4,
                        "lsb": 0,
                        "access": "rw",
                    },
                ],
            },
            "regs.blk0.reg1": {
                "type": "reg",
                "name": "regs.blk0.reg1",
                "offset": 0x4,
                "size": 0x4,
                "address": 0x4,
                "value": 0x0000000,
                "fields": [
                    {
                        "name": "f3",
                        "nbits": 8,
                        "lsb": 24,
                        "access": "rw",
                    }, {
                        "name": "f2",
                        "nbits": 8,
                        "lsb": 16,
                        "access": "rw",
                    }, {
                        "name": "f1",
                        "nbits": 8,
                        "lsb": 8,
                        "access": "rw",
                    }, {
                        "name": "f0",
                        "nbits": 8,
                        "lsb": 0,
                        "access": "rw",
                        "doc": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
                    },
                ],
            },
            "regs.blk1.reg0": {
                "type": "reg",
                "name": "regs.blk1.reg0",
                "offset": 0x0,
                "size": 0x4,
                "address": 0x1000,
                "value": 0x0badf00d,
                "fields": [
                    {
                        "name": "address",
                        "nbits": 32,
                        "lsb": 0,
                        "access": "rw",
                        "doc": "The address of the operation.",
                    },
                ],
            },
            "regs.blk1.reg1": {
                "type": "reg",
                "name": "regs.blk1.reg1",
                "offset": 0x4,
                "size": 0x4,
                "address": 0x1004,
                "value": 0x00000002,
                "fields": [
                    {
                        "name": "rsvd1",
                        "nbits": 8,
                        "lsb": 24,
                        "access": "ro",
                        "doc": "Reserved",
                    }, {
                        "name": "nbytes",
                        "nbits": 16,
                        "lsb": 8,
                        "access": "rw",
                        "doc": "The number of bytes to transmit."
                    }, {
                        "name": "rsvd0",
                        "nbits": 6,
                        "lsb": 2,
                        "access": "ro",
                        "doc": "Reserved",
                    }, {
                        "name": "done",
                        "nbits": 1,
                        "lsb": 1,
                        "access": "w1c",
                        "doc": "Set by hardware when the operation is complete.",
                    }, {
                        "name": "start",
                        "nbits": 1,
                        "lsb": 0,
                        "access": "w1s",
                        "doc": "Starts the operation. Cleared by hardware when the operation has started.",
                    },
                ],
            },
        }

        if CEF:
            self.regview = CEFRegView(self.right, width=800)
        else:
            self.regview = RegView(self.right)
        self.regview.pack(fill=BOTH, expand=TRUE, padx=(0, 5))

        self.treenav.load_items(self.items)
        self.treenav.see("regs.blk0.reg0")
        self.treenav.selection_set("regs.blk0.reg0")

        for item in self.items.values():
            if item["type"] == "reg":
                connecter.set(item["address"], item["value"])

        self.regview.load_reg(self.items.get("regs.blk0.reg0"))

        # self.regview = ttk.Frame(self.split_h)

        self.root.bind("<Control-d>", self.toggle_dock)
        import pathlib
        ico_path = pathlib.Path(__file__).parent.resolve().joinpath("chip.ico")
        try:
            self.root.iconbitmap(ico_path)
            # IDLE uses this but it looks blurry compared to iconbitmap()
            # self.root.wm_iconbitmap(default=ico_path)
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
        if CEF:
            cef.Shutdown()

# Obey Windows DPI settings
#
# This doesn't work very well.  The Treeview rendering and field name rotation don't handle well.

# Source: https://github.com/python/cpython/blob/8492b729ae97737d22544f2102559b2b8dd03a03/Lib/idlelib/pyshell.py#L14-L22
#
# Valid arguments for the ...Awareness call below are defined in the following.
# https://msdn.microsoft.com/en-us/library/windows/desktop/dn280512(v=vs.85).aspx
# import sys
# if sys.platform == 'win32':
#     try:
#         import ctypes
#         PROCESS_SYSTEM_DPI_AWARE = 1  # Int required.
#         ctypes.OleDLL('shcore').SetProcessDpiAwareness(PROCESS_SYSTEM_DPI_AWARE)
#     except (ImportError, AttributeError, OSError):
#         pass

# Fix Windows taskbar icon
#
# Source: https://stackoverflow.com/a/1552105
import sys
if sys.platform == 'win32':
    try:
        import ctypes
        myappid = u'register-explorer' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except (ImportError, AttributeError, OSError):
        pass

GUI().run()
