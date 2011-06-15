from gi.repository import Gtk

statusbar = None
window = None
tabs = ""

def set_status(string):
    if statusbar is not None:
        statusbar.get_message_area().get_children()[0].set_text(string)

def set_title(string):
    if window is not None:
        window.set_title("CILib-Tools - " + string)

def save(outFile, sections, alg=None, prob=None, m=None, sim=None):
    if not None in [alg, prob, m, sim]:
        individuals = {"algorithm": find_idref(sections["algorithm"].store, alg),
                       "problem": find_idref(sections["problem"].store, prob),
                       "measurements": find_idref(sections["measurements"].store, m),
                       "simulation": sim}

    keys = sections.keys()
    keys.sort()

    outFile.write("""<?xml version="1.0"?>\n""")
    outFile.write("""<!DOCTYPE simulator [\n""")
    outFile.write("""<!ATTLIST algorithm id ID #IMPLIED>\n""")
    outFile.write("""<!ATTLIST problem id ID #IMPLIED>\n""")
    outFile.write("""<!ATTLIST measurements id ID #IMPLIED>\n""")
    outFile.write("""]>\n\n""")
    outFile.write("""<simulator>\n""")

    for el in keys:
        inc_tab()
        if not el == "measurements":
            outFile.write("\t<" + el + "s>\n")
            inc_tab()

        if not None in [alg, prob, m, sim]:
            recurse_save(outFile, sections[el].store, individuals[el], el)
        else:
            root = sections[el].store.get_iter_first()
            while root is not None:
                recurse_save(outFile, sections[el].store, root, el)
                root = sections[el].store.iter_next(root)

        if not el == "measurements":
            outFile.write("\t</" + el + "s>\n")
            dec_tab()
        dec_tab()

    outFile.write("""</simulator>\n""")
    outFile.close()

def recurse_save(f, src, root, el):
    if el == "simulation":
        row = src.get(root, 0, 1, 2, 3, 4)
        f.write(tab() + "<simulation samples=\"" + row[3] + "\">\n")
        f.write(tab() + "\t<algorithm idref=\"" + row[0] + "\"/>\n")
        f.write(tab() + "\t<problem idref=\"" + row[1] + "\"/>\n")
        f.write(tab() + "\t<measurements idref=\"" + row[2] + "\"/>\n")
        f.write(tab() + "\t<output format=\"TXT\" file=\"" + row[4] + "\"/>\n")
        f.write(tab() + "</simulation>\n")
    else:
        row = src.get(root, 0, 1, 2, 3, 4, 5, 6)
        f.write(tab() + "<" + str(row[0]))

        if not row[5] == "":
            f.write(" id=\"" + str(row[5]) + "\"")

        if row[3] == "value":
            f.write(" value=\"" + str(row[2]) + "\"")
        elif row[3] == "":
            pass
        elif row[3] == "idref":
            f.write(" idref=\"" + str(row[2]) + "\"")
        elif row[3] == "file":
            f.write(" format=\"TXT\" file=\"" + str(row[2]) + "\"")
        else:
            f.write(" class=\"" + str(row[2]) + "\"")

        #check if must go to sublevel
        allDefault = True
        for i in range(src.iter_n_children(root)):
            lmnt = src.get_value(src.iter_nth_child(root, i), 2)
            if not (lmnt == "Default" or lmnt == "Primitive" or lmnt == "idref" or lmnt == "file"):
                allDefault = False

        if not allDefault:
            f.write(">\n")

            for i in range(src.iter_n_children(root)):
                child = src.iter_nth_child(root, i)
                lmnt = src.get(child, 2)[0]

                if not (lmnt == "Default" or lmnt == "Primitive"):
                    inc_tab()
                    recurse_save(f, src, src.iter_nth_child(root, i), el)
                    dec_tab()

            f.write(tab() + "</" + str(row[0]) + ">\n")
        else:
            f.write("/>\n")

def inc_tab():
    global tabs
    tabs = tabs + "\t"

def dec_tab():
    global tabs
    tabs = tabs[:-1]

def tab():
    global tabs
    return tabs

def find_idref(store, idref):
    it = store.get_iter_first()

    while it is not None:
        row = store.get_value(it, 5)
        if row == idref:
            return it

        it = store.iter_next(it)

    return None

