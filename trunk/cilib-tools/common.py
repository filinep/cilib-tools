from gi.repository import Gtk

statusbar = None

def set_status(string):
    if statusbar is not None:
        statusbar.get_message_area().get_children()[0].set_text(string)
