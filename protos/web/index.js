function create_td(parent, child, className = "") {
    let td = parent.insertCell()
    if (typeof(child) == "object") {
        td.appendChild(child)
    } else {
        td.innerHTML = child
    }
    if (className != "") {
        td.className = className
    }
    return td
}

function create_th(parent, text) {
    let th = document.createElement("th")
    th.appendChild(document.createTextNode(text))
    parent.appendChild(th)
    return th
}

function create_input(value) {
    let input = document.createElement("input");
    input.type = "text"
    input.value = value
    return input
}

function create_span(text) {
    let span = document.createElement("span")
    span.appendChild(document.createTextNode(text))
    return span
}

function create_layout_table(parent, fields) {
    let t = document.createElement("table");
    t.className = "layout"

    // Bit indexes row
    let th = t.createTHead();
    let tr = th.insertRow();
    for (let i = 0; i < 32; i++) {
        create_th(tr, 31 - i, "layout_bit_index")
    }

    // Field names row
    tr = t.insertRow();
    fields.forEach(function (field) {
        let span = create_span(field.name)

        let td = create_td(tr, span, "layout_field_name")
        td.colSpan = field.nbits
        if (field.name.length > 4 * field.nbits) {
            span.classList.add("rotate")
        }
   })

    // Fields values row
    tr = t.insertRow();
    fields.forEach(function (field) {
        text = function () {
            if (field.nbits == 1) {
                return "0"
            } else {
                return "0x0"
            }
        }()
        create_td(tr, create_input(text), "fieldvalue").colSpan = field.nbits
    })

    // Register value row
    tr = t.insertRow();
    create_td(tr, create_input("0x00000000"), "regvalue").colSpan = 32

    parent.appendChild(t);
}

function create_li(parent, text) {
    let li = document.createElement("li")
    li.appendChild(document.createTextNode(text))
    parent.appendChild(li)
}

function create_field_table(parent, fields) {
    let t = document.createElement("table");
    t.className = "fields"

    let th = t.createTHead()
    let tr = th.insertRow()
    create_th(tr, "Bits", "fields_nbits")
    create_th(tr, "Name", "fields_name")
    create_th(tr, "Access", "fields_access")
    create_th(tr, "Description", "fields_description")

    let tb = t.createTBody()
    fields.forEach(function (field) {
        let tr = tb.insertRow()
        let nbits = function() {
            if (field.nbits == 1) {
                return field.lsb
            } else {
                let msb = field.lsb + field.nbits - 1
                return `${msb}:${field.lsb}`
            }
        }()
        create_td(tr, nbits, "fields_nbits")
        create_td(tr, field.name, "fields_name")
        create_td(tr, field.access, "fields_access")
        let doc = function() {
            if (field.doc) {
                return field.doc.replace(/(?:\r\n|\r|\n)/g, '<br>')
            } else {
                ""
            }
        }()
        create_td(tr, doc, "fields_description")
    })

    parent.appendChild(t)
}

function load_reg(reg) {
    var reg = reg

    let layout = document.getElementById("layout")
    while (layout.firstChild) {
        layout.removeChild(layout.firstChild)
    }
    create_layout_table(layout, reg.fields)

    let fields = document.getElementById("fields")
    while (fields.firstChild) {
        fields.removeChild(fields.firstChild)
    }
    create_field_table(fields, reg.fields)
}

fields = [
    {
        "name": "f1",
        "lsb": 16,
        "nbits": 16,
        "access": "rw",
    }, {
        "name": "f0",
        "lsb": 0,
        "nbits": 16,
        "access": "rw",
    }
]

fields = [
    {
        "name": "cmd",
        "nbits": 8,
        "lsb": 24,
        "access": "rw",
        "doc": `On write:

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

IMPORTANT NOTE: Before writing a new command to this register, VCESW must first ensure that the NAND sequencer is ready to accept new commands (by polling register NANDGLBSTAT until bit nand_seq_rdy high)`,
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
        "doc": `The target LUN ID for the command.

* 0x0 - 0x7 -- Select single specified LUN (8 LUNs per NAND sequencer)
* 0xF -- Broadcast to all 8 LUNs
* 0x8 - 0xE -- Equivalent to 0x0 - 0x7 respectively.`,
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
        "doc": `Select the mode for the DONE_IRQ:

* 0 -- DONE_IRQ will fine upon command completion for any command (batch and direct commands)
* 1 -- DONE_IRQ will only fire upon batch command completion`,
    }, {
        "name": "tmo_sel",
        "nbits": 2,
        "lsb": 6,
        "access": "rw",
        "doc": `Select the timeout value.

* 0x0 -- Timeout after 4ms (exactly 3.93ms)
* 0x1 -- Timeout after 8ms (exactly 7.86ms)
* 0x2 -- Timeout after 32ms (exactly 31.46ms)
* 0x3 -- Timeout after 4ms (exactly 3.93ms)`,
    }, {
        "name": "continue_on_abort_fail",
        "nbits": 6,
        "lsb": 0,
        "access": "rw",
        "doc": `Set high individual bits if you want the design to continue to the next command in the batch upon encountering abort or other failure condition. Design will not execute the command resulting in the abort/failure condition but will resume normal execution by skipping to the next command in the batch. Each bit controls continue/terminate for 1 condition.

* Bit 5 -- Continue on page-erased-verify failure (some page data non-FFs)
* Bit 4 -- Continue on DBE on READ command
* Bit 3 -- Continue on program/erase failure (e.g. on access to a bad block)
* Bit 2 -- Continue on write protect violation (abort_id 0xB)
* Bit 1 -- Continue on timeout (fail_id 0x1)
* Bit 0 -- Continue on bad descriptor (abort_ids 0x3-0xA)

If all bits low, the design will stop upon any abort/failure condition described above and will not execute any of the following commands scheduled in the batch. Regardless of bits set in this field, the design will never continue upon abort conditions 0x1, 0x2 (illegal command in NANDCMDR.nand_cmd or 0 in NANDNCMDS.nand_ncmds).`,
    }
]

create_layout_table(document.getElementById("layout"), fields)
create_field_table(document.getElementById("fields"), fields)
