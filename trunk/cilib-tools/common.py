from gi.repository import Gtk

statusbar = None
window = None

def set_status(string):
    if statusbar is not None:
        statusbar.get_message_area().get_children()[0].set_text(string)

def set_title(string):
    if window is not None:
        window.set_title("CILib-Tools - " + string)

def write_xml_header(outFile):
    outFile.write("""<?xml version="1.0"?>\n""")
    outFile.write("""<!DOCTYPE simulator [\n""")
    outFile.write("""<!ATTLIST algorithm id ID #IMPLIED>\n""")
    outFile.write("""<!ATTLIST problem id ID #IMPLIED>\n""")
    outFile.write("""<!ATTLIST measurements id ID #IMPLIED>\n""")
    outFile.write("""]>\n\n""")
