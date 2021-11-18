#!/usr/bin/env python3
# This Python file uses the following encoding: utf-8

from pathlib import Path
from pprint import pprint, pformat
import fitz, os, queue, sys
from .fitzcli import main as fitzGetText

from PySide6.QtWidgets import QApplication, QFileDialog, QWidget, QRadioButton, QTextEdit
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QFile, Qt, QCoreApplication, QEvent
from PySide6.QtUiTools import QUiLoader

class MetadataEditor(QWidget):
    def __init__(self):
        super(MetadataEditor, self).__init__()

        self.docsList = []
        self.metadata = {} 
        self.load_ui()
                
        # style sheets give another way of signalling UI state - If I can ever figure out such good way.
        #self.setStyleSheet("QLabel { color: rgb(50, 50, 50); font-size: 11px; background-color: rgba(188, 188, 188, 50); border: 1px solid rgba(188, 188, 188, 250); } QSpinBox { color: rgb(50, 50, 50); font-size: 11px; background-color: rgba(255, 188, 20, 50); }" 
        #self.ui.pdf_bmp_label = QImage(531, 666, QImage.Format_ARGB32) #.setPixmap(100, 100)

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "metadata.ui")
        if not path:
            return None
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)

        self.ui = None
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        # connect the page navigation push buttons
        self.ui.commit_pushButton.clicked.connect(self.commit_check)
        self.ui.back_pushButton.clicked.connect(self.go_back)
        self.ui.next_pushButton.clicked.connect(self.go_next)
        self.ui.quit_pushButton.clicked.connect(self.quit)

        # connect the fitzcli gettext radio buttons
        for w in self.findChildren(QRadioButton):
            w.clicked.connect(self.BtnSelected)

        # connect the textedit input fields to a common function
        for w in self.findChildren(QTextEdit):
            if w.objectName().endswith("Edit"):
                w.textChanged.connect(self.EditSelected)
                w.installEventFilter(self)
                w.get = w.toPlainText

        # qline edit is slightly different, sigh
        # we are setting "get" to "text"

        self.ui.rename_lineEdit.textChanged.connect(self.EditSelected)
        self.ui.rename_lineEdit.installEventFilter(self)
        self.ui.rename_lineEdit.get = self.ui.rename_lineEdit.text

        # date is basically read only so no event filter
        self.ui.date_lineEdit.textChanged.connect(self.EditSelected)
        self.ui.date_lineEdit.get = self.ui.date_lineEdit.text

        self.initialize_editButtons()
        self.newname = False


    def checkNewFileName(self, fn):
        newname = fn+'.pdf'
        r, f = self.docsList[self.docsList_current]
        trial = not os.path.isfile(os.path.join(r, newname))
        return trial, newname

    def eventFilter(self, obj, event):
        """ Catch the keyboard Enter key event and use it to 
            Commit the Title - for further processing in the 
            pdf file rename function.
            Commit the rename - this actually just prepares, the 
            actual rename happens after the Pdf is saved. 
        """

        if event.type() == QEvent.KeyPress and obj.hasFocus() :
                # print(event.type())
                weAre =  obj.objectName()
                key = weAre[0:weAre.find('_')]
                # get() resolves to the right text retrieve function
                data = obj.get()
                #if key == 'title':
                #    print(key)
            
                #data = obj.toPlainText()

                # print(data)
                # print(self.metadata)
                #self.metadata[key] = data
                # print(f'Enter {key} pressed')

                if event.key() == Qt.Key_F3 and key == 'title':
                    data =  data.title().replace(' ', '').replace('/', '-')
                    self.ui.rename_lineEdit.setText(data)
                    return True
                    
                elif event.key() == Qt.Key_Return and (key == 'title' or key == 'author'):
                    data =  data.title()
                    obj.setPlainText(data)
                    return True

                elif event.key() == Qt.Key_Return and key == 'rename' :
                    status, newname = self.checkNewFileName(data)
                    if status :
                        # proposed file name is ok, save for later
                        self.newname = newname
                    else:
                        # same named file already exists, clear to signal restart naming needed
                        self.ui.rename_lineEdit.clear()
                    return True
                                                      
        return super().eventFilter(obj, event)
        

    def initialize_editButtons(self):
        # reset the edit fields back to their placeholder strings.
        self.ui.author_textEdit.clear()
        self.ui.title_textEdit.clear()
        self.ui.keywords_textEdit.clear()
        self.ui.date_lineEdit.clear()

        self.ui.commit_pushButton.setEnabled(False)
    
    def go_back(self) : 
        self.docsList_current = self.docsList_current -1
        self.processPdf()


    def go_next(self) : 
        self.docsList_current = self.docsList_current +1
        self.processPdf()

    def commit_check(self):
        # missing some sanity checking here!
        self.update_metadata()
        # print("back from check")

    def BtnSelected(self, event, ) :
        # Change the call to fitzcli requesting different layout processing.
        try:
            genAllRadioButtons = self.findChildren(QRadioButton)
            mode = ([rb.text() for rb in genAllRadioButtons if rb.isChecked()][0]).lower()
            
            # set some command line arguments for the call to fitzcli
            fo = "cause I can't make it use a string.io object"
            sys.argv = [sys.argv[0], 'gettext', "-mode", mode, "-pages", "1", "-output",fo, self.fn]
            fitzGetText()       # calls the main() function with above args.
            # paste the output into a browser window widget
            self.ui.textBrowser.setText(open(fo, "r").read())
        
        except Exception as e:
            print(e)


    def EditSelected(self) :
        try:
            x = self.sender()
            widgetKey = x.objectName()
            #ourKey = self.sender().objectName()
            metaKey = widgetKey[:widgetKey.find("_")]
            data = x.get()
            # print("meta was ", self.metadata)
       
            if metaKey == 'date':
                metaKey = 'creationDate'

            if metaKey != 'rename':
                self.metadata[metaKey] = data
                # print(f' New .{metaKey}. is .{data}.')

            self.ui.commit_pushButton.setEnabled(True)
           
        except Exception as e:
            print(e)

    
    def update_metadata(self):
        try:
            # deug log to terminal
            pprint(self.metadata)
            # do an incremental update, no error checks!
            self.doc.set_metadata(self.metadata) 
            if (self.doc.can_save_incrementally()):
                self.doc.saveIncr()
            else:
                dst = self.fn + ".tmp"
                self.doc.save(dst)
                os.rename(self.fn, self.fn + ".original")
                os.rename(dst, self.fn)

            self.doc.close()

            if self.newname != False:
                # now we need to actually rename it.  Should be ok now that 
                # fitz is closed.
                dir, fn = self.docsList[self.docsList_current]

                os.rename(self.fn, os.path.join(dir, self.newname))

                x = self.docsList[self.docsList_current]
                self.docsList[self.docsList_current] = [ x[0], self.newname ]
                # print(x)
        except Exception as e:
            print(e)

    def setEditData(self, metadata):
        # get the metadata found on reading the pdf and insert it into
        # the edit fields.

        # uninterpreted label shows what we came in with.
        self.ui.metadata_label.setText(pformat(metadata)[1:-1])
        # initialize some flags
        self.date_set = self.title_set = self.author_set = self.keywords_set = False
        
        # parse out the data and put into the widget entry fields
        for key in metadata:
            k = key.lower()
            if k == "author":
                self.ui.author_textEdit.setPlainText(metadata[key])

            elif k == "keywords":
                self.ui.keywords_textEdit.setPlainText(metadata[key])

            elif k == "subject":
                self.ui.subject_textEdit.setPlainText(metadata[key])

            elif k == "creationdate":
                self.ui.date_lineEdit.setText(metadata[key])

            elif k == "title":
                self.ui.title_textEdit.setPlainText(metadata[key])
            

    def processPdf(self) :
        self.initialize_editButtons()   # clear the entry fields to their placeholder strings.
        
        # get a path to a pdf  to work on
        dir, fn = self.docsList[self.docsList_current]
        path = self.fn = os.path.join(dir, fn)

        # display the pdf file name
        self.ui.path_label.setText(f"{fn}")

        # preset the rename file widget to the original file name.
        self.ui.rename_lineEdit.setText(f"{fn[:-4]}")

        # set up the file list navigation buttons
        # this logic allows up or down moves through the list,
        # but no wrap around modulo stuff.
        if self.docsList_top > self.docsList_current +1 :
            self.ui.next_pushButton.setEnabled(True)
        else:
            self.ui.next_pushButton.setEnabled(False)
        if self.docsList_current > 0 :
            self.ui.back_pushButton.setEnabled(True)
        else:
            self.ui.back_pushButton.setEnabled(False)
        
        # make a file progress label
        pos = f"{(self.docsList_current +1)} / {len(self.docsList)} "
        self.ui.filePosition.setText(pos)

        # At last we can start processing the pdf!    
        try:

            #fin = '/mnt/Marcs80GB/Reiserfs1/Kubo/3DCS \udca5ѥ\udcf3\udca5\udcd5ura.pdf'
            # turns out that 
            #stream_buffer = open(path, "rb").read()
            #doc = fitz.open("pdf", stream_buffer)

            #path = bytes(Path(path))
            # Actually, let PyMuPDF call on MuPDF to do the work!
            # building on the stout shoulders of our betters.
            self.doc = doc = fitz.open(path)



            page = doc.loadPage(0)

            # get the metadata - our whole purpose is to update it!
            self.metadata = doc.metadata
            self.setEditData(self.metadata)

            # display page 0 in text strings
            text = page.getText()           # output = plain text by default
            self.ui.textBrowser.setText(text)

            # now get a properly rendered bitmap of the pdf document, page 0 only.
            pno = 0
            pix = doc.get_page_pixmap(pno)

            # adjust image size to fit the GUI         
            width, height = pix.w, pix.h
            w_vue, h_vue = self.ui.pdf_bmp_label.width(), self.ui.pdf_bmp_label.height()
            png = pix.tobytes(output="png")

            qimage = QImage()
            qimage.loadFromData(png, "PNG")
            self.ui.pdf_bmp_label.setPixmap(QPixmap.fromImage(qimage))

            # Commit was enabled at each of the above metadata value settings. 
            # want to wait for changes from now on.
            self.ui.commit_pushButton.setEnabled(False)

        except Exception as e :
            print(e)


    def quit(self): 
        """ Quit button handler. """
        self.close()

    def keyPressEvent(self, e):
        """  Escape key is a quick bail-out. """
        if e.key() == Qt.Key.Key_Escape:
                self.close()


def EditorMain():    
    # attempt to quiet some error messages.
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication([])
    widget = MetadataEditor()

    # just sets the window title, the expected qt designer ui ways didn't work.
    widget.setWindowTitle('Quick and Dirty PDF Metadata Editor')
    
    '''
    Options for single argument:
    1. relative or absolute path to a single pdf file - just process it
    2. path is a directory, do a filesystem walk and collect .pdf files found into a work list
    3. no arguments - open a qt directory chooser and then process as in 2.
    '''

    if len(sys.argv) == 1 :                 # no calling arguments, open a directory chooser
         path = QFileDialog.getExistingDirectory(widget, ("Open Top Level PDF Directory"),None,
                                    #"/home",
                                    QFileDialog.ShowDirsOnly
                                    | QFileDialog.DontResolveSymlinks)

    if len(sys.argv) == 2:
        path = os.fspath(Path(__file__).resolve().parent / sys.argv[1])
        if os.path.isfile(path) :           # case of only single file to process
            dir, fn = os.path.split(path)
            widget.docsList.append([dir, fn])
            widget.docsList_top = 1
            widget.docsList_current = 0

    if len(widget.docsList) == 0:
        for root, dirs, files in os.walk(path) :
            for fn in files:
                if fn.lower().endswith("pdf"):
                    widget.docsList.append([root, fn])
        widget.docsList_top = len(widget.docsList)
        widget.docsList_current = 0
    
    print( "This is what we'll look at first: ", widget.docsList[0])

    widget.show()
    widget.processPdf()
    sys.exit(app.exec())

if __name__ == "__main__":
    EditorMain()
