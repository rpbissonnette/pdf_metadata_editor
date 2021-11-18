
![This is a screen capture](file://Screenshot.png)

# Quick and Dirty PDF metadata Editor

## Allows copy and paste from the pdf into entry widgets that get copied into the metadata on save.

Uses PyMuPDF and then MuPDF to do the hard work working with pdfs.
Uses PySide6 and thence the Qt libraries to handle the GUI bits.

So this is just a 300 something line script tying them together.

### Usage:

In the src/pdf_metadata_editor directory, you can just call it thusly:

python metadata.py  arg

Where arg can either:
    1. name a single pdf
    2. name a directory to begin editing all the pdfs thereunder
    3. with no argument a file chooser 

On startup a list of target pdfs is created, and the GUI "next" and "back" push buttons
Copy and paste Title, Author from the center pane.
Add keywords and subject.

The right panel shows what the actual pdf rendering is, unfortuantely you can't select and copy from it.

Click on "Commit" to write the changes out.

#### Hidden functions

In the Title widget, the "Enter" key will convert to "Title" format - words begin with captials.
In the Title widget, F3 copies the title format to the Rename widget
In the Rename widget, the "Enter" key will request the pdf file name to be renamed after changes are committed.
    if the rename would fail, the entry widget is cleared.

In the center panel, you can change the text display with the 3 radio buttons.  Just try and see if
you get something more useful.

##  How to make
Maybe something like this might work:

git clone https://github.com/rpbissonnette/pdf_metadata_editor.git

Then if build tools are installed:
python -m build

Then pip install _path_to_the_whl file.

##  How to install 

Best to use a virtual environment  - PySide is going to download a ton of Qt libraries...

pip install ~/pdf_metadata_editor/dist/PdfMetadataEditor-0.0.1-py3-none-any.whl 
    replace the argument with the real path on your machine.

If it didn't work, and like me you don't remember how to upgrade, just uninstall
    pip uninstall ~/pdf_metadata_editor/dist/PdfMetadataEditor-0.0.1-py3-none-any.whl 

##  How to run
    python -m pdf_metadata_editor optional_args_go_here

# Major deficiencies

1.  PyMuPdf / fitz.open can't deal with broken pathnames.  Ie, I have some with what look like 
unicode surrogates that can't be utf-8 encoded.  

They come from an os.walk and putting the file name through Path lets me access the raw binary. 
I can open that and read it into a stream that fitz is happy with, but I don't know how to do an incremental save in such a case.

2. UI is klunky and needs help.

3. Sizes are all fixed and don't adjust for your screen size.

4. Would be nice to use style sheets to help the user understand the processing state.

5. Packaging is just starting.  __main__.py is duplicating code needlessly.
