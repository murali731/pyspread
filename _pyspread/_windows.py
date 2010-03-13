#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6 on Sun May 25 23:31:23 2008

# Copyright 2008 Martin Manns
# Distributed under the terms of the GNU General Public License
# generated by wxGlade 0.6 on Mon Mar 17 23:22:49 2008

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------


"""
_windows
========

Provides:
---------
  1. MainWindow: Main window of the application pyspread

"""

import bz2
import os
import csv
import cPickle as pickle
import sys
import types

import wx
import wx.aui
import wx.grid
import wx.html
import wx.lib.agw.genericmessagedialog as gmd

import _pyspread._printout as printout

import _pyspread._grid as _grid

from _pyspread._menubars import MainMenu
from _pyspread._toolbars import MainToolbar, FindToolbar, AttributesToolbar
from _pyspread._dialogs import MacroDialog, CsvImportDialog, CsvExportDialog, \
            DimensionsEntryDialog, AboutDialog
from _pyspread._interfaces import CsvInterfaces, PysInterfaces, \
            string_match, bzip_dump, is_pyme_present, genkey, sign, verify
from _pyspread.config import ICONPREFIX, icon_size, KEYFUNCTIONS
            


class MainWindow(wx.Frame):
    """Main window of pyspread
    
    Parameters:
    -----------
    dimensions: 3-tuple of int, defaults to (100, 100, 1)
    \tDimensions of the grid
    
    """
    def __init__(self, *args, **kwds):
        try:
            dim = kwds.pop("dimensions")
        except KeyError:
            dim = (1000, 100, 1)
        
        self.wildcard = "Pyspread file (*.pys)|*.pys|" \
                        "All files (*.*)|*.*"
        self.wildcard_interfaces = {0: PysInterfaces, 
                                    1: PysInterfaces}
        # Get path of module
        self.module_path = os.path.dirname(__file__)
        
        # Code execution flag
        self.code_execution = True
        
        # Default interface
        self.wildcard_interface = self.wildcard_interfaces[0]
        
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        
        self._mgr = wx.aui.AuiManager(self)
        
        # Menu Bar
        self.main_window_menubar = wx.MenuBar()
        self.main_menu = MainMenu(parent=self, menubar=self.main_window_menubar)
        self.SetMenuBar(self.main_window_menubar)
        
        # Status bar
        self.main_window_statusbar = self.CreateStatusBar(1, wx.ST_SIZEGRIP)
        
        # Main tool bar
        self.main_window_toolbar = MainToolbar(self, -1)
        
        # Combo box for table choice
        self.cb_id = wx.NewId()
        self.cbox_z = wx.ComboBox(self.main_window_toolbar, self.cb_id, "0", \
                      size=(icon_size[0]*2, icon_size[1]-4), \
                      style=wx.CB_DROPDOWN)
        self.main_window_toolbar.AddControl(self.cbox_z)
        self.main_window_toolbar.Realize()
        
        # Main grid
        self.MainGrid = _grid.MainGrid(self, -1, size=(1, 1), dim=dim, \
            set_statustext=self.main_window_statusbar.SetStatusText, 
            cbox_z = self.cbox_z)
        
        # Find tool bar
        self.find_toolbar = FindToolbar(self, -1)
        
        # Attributes tool bar
        self.attributes_toolbar = AttributesToolbar(self, -1)
        
        # Disable menu item for leaving save mode
        file_approve_menuitem = self.main_menu.methodname_item["OnFileApprove"]
        file_approve_menuitem.Enable(False)
        
        # Print data
        # wx.PrintData properties setup from 
        # http://aspn.activestate.com/ASPN/Mail/Message/wxpython-users/3471083
        self.print_data = wx.PrintData()
        self.print_data.SetPaperId(wx.PAPER_A4)
        self.print_data.SetPrintMode(wx.PRINT_MODE_PRINTER)
        self.print_data.SetOrientation(wx.LANDSCAPE)
        #self.print_data_margins = (wx.Point(15, 15), wx.Point(15, 15))
        
        self._set_properties()
        self._do_layout()
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_FIND, self.OnFind)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFind)
        self.Bind(wx.EVT_FIND_REPLACE, self.OnFind)
        self.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnFind)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
        self.Bind(wx.EVT_TEXT, self.MainGrid.OnCombo, id=self.cb_id)
        self.Bind(wx.EVT_COMBOBOX, self.MainGrid.OnCombo, id=self.cb_id)
        wx.EVT_KEY_DOWN(self.MainGrid, self.OnKey)
        
        # Misc
        self.MainGrid.mainwindow = self
        self.MainGrid.deletion_imminent = False
        self.filepath = None # No file loaded yet
        self.borderstate = "AllBorders" # For color and width changes
    
    def _set_properties(self):
        """Setup title, icon, size, scale, statusbar, main grid"""
        
        self.SetTitle("pyspread")
        _icon = wx.EmptyIcon()
        _icon.CopyFromBitmap(wx.Bitmap(ICONPREFIX+'icons/pyspread.png', \
                             wx.BITMAP_TYPE_ANY))
        self.SetIcon(_icon)
        
        self.SetInitialSize((1000, 700))
        self.Maximize()
        
        # Status bar
        
        self.main_window_statusbar.SetStatusWidths([-1])
        
        # Scale for Custom Renderer drawn content (needs TableBase!!)
        self.scale = 1.0
        
        # statusbar fields
        main_window_statusbar_fields = [""]
        for i in range(len(main_window_statusbar_fields)):
            self.main_window_statusbar.SetStatusText( \
                            main_window_statusbar_fields[i], i)
        self.main_window_toolbar.SetToolBitmapSize(icon_size)
        self.main_window_toolbar.SetMargins((1, 1))
        self.main_window_toolbar.Realize()
    
    def _do_layout(self):
        """Adds widgets to the wx.aui manager and controls the layout"""
        
        # Add the toolbars to the manager
        self._mgr.AddPane(self.main_window_toolbar, wx.aui.AuiPaneInfo().
                          Name("main_window_toolbar").Caption("Main Toolbar").
                          ToolbarPane().Top().Row(0).CloseButton(False).
                          LeftDockable(False).RightDockable(False))
                                  
        self._mgr.AddPane(self.find_toolbar, wx.aui.AuiPaneInfo().
                          Name("find_toolbar").Caption("Find").
                          ToolbarPane().Top().Row(1).MaximizeButton(False).
                          LeftDockable(False).RightDockable(False))
        
        self._mgr.AddPane(self.attributes_toolbar, wx.aui.AuiPaneInfo().
                          Name("attributes_toolbar").Caption("Cell Attributes").
                          ToolbarPane().Top().Row(1).MaximizeButton(False).
                          LeftDockable(False).RightDockable(False))
                          
        self._mgr.AddPane(self.MainGrid.entry_line, wx.aui.AuiPaneInfo().
                          Name("entry_line").Caption("Entry line").
                          ToolbarPane().MinSize((800, 10)).Row(2).
                          Top().CloseButton(False).MaximizeButton(False).
                          LeftDockable(False).RightDockable(False))
        
        # Add the main grid
        self._mgr.AddPane(self.MainGrid, wx.CENTER)
        
        # Hide panes initially
        #self._mgr.GetPane("find_toolbar").Hide()
        
        # Tell the manager to 'commit' all the changes just made
        self._mgr.Update()
        
    def OnClose(self, event):
        """Deinitialize the frame manager"""
        
        self._mgr.UnInit()
        # delete the frame
        self.Destroy()
    
    def OnKey(self, event):
        """
        Additional key behavior if not already in menu
        
        The method parses the key representation and calls the respective
        function for the defined keys. It relies on the KEYFUNCTIONS dict in
        config.py and on self.key_modifier_methods. Note that menu defined keys
        are not evaluated.
        
        """
        
        # Key modifier event methods
        kmm = {'Ctrl': 'event.ControlDown()', \
               'not_Ctrl': 'not event.ControlDown()', \
               'Shift': 'event.ShiftDown()', \
               'not_Shift': 'not event.ShiftDown()'}
        
        for keystr, funcstr in KEYFUNCTIONS.iteritems():
            keys = keystr.split('+')
            
            # Actual unmodified key in KEYFUNCTIONS
            actkey = keys.pop() 
            evtmeths = [kmm[modifier] for modifier in keys]
            evtmeths += [" == ".join(["event.GetKeyCode()", repr(ord(actkey))])]
            evtmeths_string = " and ".join(evtmeths)
            if eval(evtmeths_string):
                funccallstr = "".join(["self.", funcstr, "()"])
                eval(funccallstr)
        
        # Skip other Key events
        if event.GetKeyCode():
            event.Skip()
    
    def OnFileNew(self, event):
        """Creates a new grid and destroys the old one"""
        
        dim_dialog = DimensionsEntryDialog(self)
        if dim_dialog.ShowModal() != wx.ID_OK:
            dim_dialog.Destroy()
            return False
        
        dim_dialog.Destroy()
        
        dimensions = tuple(dim_dialog.dimensions)
        
        self.Destroy()
        self = MainWindow(None, dimensions=dimensions)
        self.Show()
        
        self.MainGrid.pysgrid.unredo.reset()
    
    def validate_signature(self, filename):
        """Returns True if a valid signature is present for filename"""
        
        sigfilename = filename + '.sig'
        
        try:
            dummy = open(sigfilename)
            dummy.close()
        except IOError:
            # Signature file does not exist
            return False
        
        # Check if the sig is valid for the sigfile
        return verify(sigfilename, filename)
    
    def OnFileOpen(self, event):
        """Opens file dialog and loads file"""
        
        dlg = wx.FileDialog(
            self, message="Choose a file", defaultDir=os.getcwd(),
            defaultFile="", wildcard=self.wildcard, \
            style=wx.OPEN | wx.CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            self.filepath = dlg.GetPath()
            wildcard_no = dlg.GetFilterIndex()
            self.wildcard_interface = self.wildcard_interfaces[wildcard_no]()
            
            # Set safe mode if signature missing of invalid
            if self.validate_signature(self.filepath):
                self.MainGrid.pysgrid.safe_mode = False
                self.main_window_statusbar.SetStatusText( \
                    "Valid signature found. File is trusted.")
            else:
                self.MainGrid.pysgrid.safe_mode = True
                self.main_window_statusbar.SetStatusText( \
                    "File is not properly signed. Safe mode activated. " + \
                    "Select File -> Approve to leave safe mode.")
                # Disable menu item for leaving save mode
                file_approve_menuitem = \
                    self.main_menu.methodname_item["OnFileApprove"]
                file_approve_menuitem.Enable(True)
                
            try:
                self.MainGrid.loadfile(self.filepath, self.wildcard_interface)
            except IOError:
                msg =  "Could not read file " + self.filepath
                dlg = gmd.GenericMessageDialog(self, msg, 'File read error',
                    wx.CANCEL | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            
            self.MainGrid.OnCombo(event)
            self.MainGrid.ForceRefresh()
        dlg.Hide()
        dlg.Destroy()
    
    def sign_file(self):
        """Signs file if possible"""
        
        if is_pyme_present() and self.code_execution:
            signature = sign(self.filepath)
            signfile = open(self.filepath + '.sig','wb')
            signfile.write(signature)
            signfile.close()
        else:
            msg = 'Cannot sign the file. Maybe PyMe is not installed.'
            dlg = gmd.GenericMessageDialog(self, msg, 'Cannot sign file!',
                wx.CANCEL | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
    
    def OnFileSave(self, event):
        """Saves an existing file"""
        
        if self.filepath is None:
            self.OnFileSaveAs(event)
        else:
            self.MainGrid.savefile(self.filepath, self.wildcard_interface)
            if self.MainGrid.pysgrid.safe_mode:
                self.main_window_statusbar.SetStatusText("Untrusted file saved")
            else:
                self.sign_file()
                self.main_window_statusbar.SetStatusText( \
                    "File saved and sigend")
    
    def OnFileSaveAs(self, event):
        """Opens the file dialog and saves the file to the chosen location"""
        
        dlg = wx.FileDialog( \
            self, message="Save file as ...", defaultDir=os.getcwd(), \
            defaultFile="", wildcard=self.wildcard, style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filepath = dlg.GetPath()
            wildcard_no = dlg.GetFilterIndex()
            self.wildcard_interface = self.wildcard_interfaces[wildcard_no]()
            
            self.MainGrid.savefile(self.filepath, self.wildcard_interface)
            if self.MainGrid.pysgrid.safe_mode:
                self.main_window_statusbar.SetStatusText("Untrusted file saved")
            else:
                self.sign_file()
                self.main_window_statusbar.SetStatusText( \
                    "File saved and sigend")
        
        dlg.Hide()
        dlg.Destroy()
    
    def OnFileImport(self, event): # wxGlade: MainWindow.<event_handler>
        """Imports files. Currently only CSV files supported"""
        
        # File choice
        try:
            path, filterindex = self._getfilename( \
                    message="Import file", \
                    defaultDir=os.getcwd(), \
                    defaultFile="", \
                    wildcard=" CSV file|*.*|Tab-delimited text file|*.*", \
                    style=wx.OPEN | wx.CHANGE_DIR)
        except TypeError:
            return 0
        
        csvfilename = os.path.split(path)[1]
        
        # CSV import option choice
        try:
            filterdlg = CsvImportDialog(self, csvfilepath=path)
        except csv.Error, err:
            msg = csvfilename + '" does not seem to be a valid CSV file.' + \
                '\n \nOpening it yielded the error:\n' + str(err)
                
            dlg = gmd.GenericMessageDialog(self, msg, 
                'Error opening CSV file', style=wx.ID_CANCEL | wx.ICON_ERROR)
            
            dlg.ShowModal()
            dlg.Destroy()
            return False
        
        # Get target types
        if filterindex == 0:
            if filterdlg.ShowModal() == wx.ID_OK:
                dialect, has_header = filterdlg.csvwidgets.get_dialect()
                digest_types = filterdlg.grid.dtypes
            else:
                filterdlg.Destroy()
                return 0
        elif filterindex == 1:
            dialect = csv.get_dialect('excel-tab')
            digest_types = [types.StringType]
            has_header = False
        
        filterdlg.Destroy()
        
        # The actual data import
        csv_interface = CsvInterfaces(path, dialect, digest_types, has_header)
        topleftcell = tuple(list(self.MainGrid.get_currentcell()) + \
                            [self.MainGrid.current_table])
        try:
            csv_interface.read(self.MainGrid.pysgrid, key=topleftcell)
        except ValueError, err:
            msg = 'The file "' + csvfilename + '" has only been loaded ' + \
                'partly. \n \nError message:\n' + str(err)
                
            dlg = gmd.GenericMessageDialog(self, msg, 
                'Error reading CSV file', style=wx.ID_OK | wx.ICON_INFORMATION)
            
            dlg.ShowModal()
            dlg.Destroy()
        self.MainGrid.ForceRefresh()
    
    def OnFileExport(self, event):
        """Exports files. Currently only CSV files supported"""
        
        # Get Selection --> iterable
        selection = self.MainGrid.get_selection()
        if len(selection) == 1:
            slice_x, slice_y = self.MainGrid.get_visiblecell_slice()[:2]
            selection = [(x, y) for x in xrange(slice_x.start, slice_x.stop)
                                for y in xrange(slice_y.start, slice_y.stop)]
        
        rowslice, colslice = self.MainGrid.get_selected_rows_cols(selection)
        data = self.MainGrid.getselectiondata(self.MainGrid.pysgrid, \
                                    rowslice, colslice, omittedfield_repr=' ')
                                    
        # Get CSV export options via dialog
        filterdlg = CsvExportDialog(self, data=data)
        
        if filterdlg.ShowModal() == wx.ID_OK:
            dialect, has_header = filterdlg.csvwidgets.get_dialect()
            digest_types = [types.StringType]
        else:
            filterdlg.Destroy()
            return 0
        
        filterdlg.Destroy()
        
        # Get target file path
        
        path = None
        try:
            path, filterindex = self._getfilename( \
                    message="Export file", \
                    defaultDir=os.getcwd(), \
                    defaultFile="", \
                    wildcard=" CSV file|*.*", \
                    style=wx.OPEN | wx.CHANGE_DIR)
        
        except TypeError:
            return 0
        
        # Export file
        csv_interface = CsvInterfaces(path, dialect, digest_types, has_header)
        try:
            csv_interface.write(data)
        except IOError, err:
            msg = 'The file "' + path + '" could not be fully written ' + \
                  '\n \nError message:\n' + str(err)
                  
            dlg = gmd.GenericMessageDialog(self, msg, 
                'Error writing CSV file', style=wx.ID_OK | wx.ICON_ERROR)
                
            dlg.ShowModal()
            dlg.Destroy()

    def OnFileApprove(self, event):
        """Signs the current file and leaves safe mode"""
        
        if not self.MainGrid.pysgrid.safe_mode:
            return None
        
        # The file can damage the system --> Ask again
        from config import file_approval_warning as warning
        
        dlg = gmd.GenericMessageDialog(self, warning, "Security warning",
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if dlg.ShowModal() == wx.ID_YES:
            proceed = True
        else:
            proceed = False
        dlg.Destroy()

        if proceed:
            # Leave safe mode
            self.MainGrid.pysgrid.safe_mode = False
            
            # Sign file
            self.sign_file()
            self.main_window_statusbar.SetStatusText("File saved and sigend")
            
            # Hide Menu item
            menuitem = event.GetEventObject().FindItemById(event.Id)
            menuitem.Enable(False)
            
            # Refresh grid
            self.MainGrid.ForceRefresh()
    
    def OnFilePrint(self, event):
        """Displays print dialog"""
        
        pdd = wx.PrintDialogData(self.print_data)
        #print self.print_data.GetOrientation() == wx.LANDSCAPE
        
        #print dir(pdd)
        
        printer = wx.Printer(pdd)
        
        selection = self.MainGrid.get_selection()
        if len(selection) == 1:
            slice_x, slice_y = self.MainGrid.get_visiblecell_slice()[:2]
            selection = [(x, y) for x in xrange(slice_x.start, slice_x.stop-1)
                                for y in xrange(slice_y.start, slice_y.stop-1)]
        
        rowslice, colslice = self.MainGrid.get_selected_rows_cols(selection)
        tab = self.MainGrid.current_table
        canvas = printout.MyCanvas(self, self.MainGrid, 
                                   rowslice, colslice, tab)
        
        __printout = printout.MyPrintout(canvas)

        if not printer.Print(self, __printout, True):
            pass
        else:
            self.print_data = \
                wx.PrintData(printer.GetPrintDialogData().GetPrintData())
        
        __printout.Destroy()
        canvas.Destroy()
    
    def OnExit(self, event):
        """Exit program"""
        
        sys.exit()
        event.Skip()
    
    def OnCut(self, event): 
        """Cut from main grid to clipboard"""
        
        self.MainGrid.cut()
        self.MainGrid.pysgrid.unredo.mark()
        event.Skip()
    
    def OnCopy(self, event):
        """Copy from main grid to clipboard"""
        
        self.MainGrid.copy(source=self.MainGrid.pysgrid.sgrid)
        self.MainGrid.pysgrid.unredo.mark()
        event.Skip()
    
    def OnCopyResult(self, event):
        """Copy results from main grid to clipboard"""
        
        self.MainGrid.copy(source=self.MainGrid.pysgrid)
        self.MainGrid.pysgrid.unredo.mark()
        event.Skip()
    
    def OnPaste(self, event):
        """Paste from clipboard to main grid"""
        
        self.MainGrid.paste()
        self.MainGrid.pysgrid.unredo.mark()
        event.Skip()
    
    def _launch_help(self, filename):
        """Generix help launcher"""
        
        # Set up window
        
        help_window = wx.Frame(self, -1, "Pyspread help", 
                                   wx.DefaultPosition, wx.Size(600, 500))
        help_htmlwindow = wx.html.HtmlWindow(help_window, -1, 
                            wx.DefaultPosition, wx.Size(600, 500))
        
        # Get help data
        current_path = os.getcwd()
        os.chdir(self.module_path)
        help_file = open(filename, "r")
        help_html = help_file.read()
        help_file.close()
        
        # Show tutorial window
        
        help_htmlwindow.SetPage(help_html)
        help_window.Show()
        
        os.chdir(current_path)
    
    def OnManual(self, event):
        """Launches pyspread manual"""
        
        self._launch_help("doc/manual.html")
    
    def OnTutorial(self, event):
        """Launches pyspread tutorial"""
        
        self._launch_help("doc/tutorial.html")
        
    def OnFAQ(self, event):
        """Launches pyspread FAQ"""
        
        self._launch_help("doc/faq.html")
    
    def OnAbout(self, event):
        """Launches about dialog"""
        
        about_dialog = AboutDialog(self)
    
    def OnInsertRows(self, event): # wxGlade: MainWindow.<event_handler>
        """Insert the maximum of 1 and the number of selected rows"""
        self.MainGrid.insert_selected_rows()
        event.Skip()
    
    def OnInsertColumns(self, event): # wxGlade: MainWindow.<event_handler>
        """Inserts the maximum of 1 and the number of selected columns """
        self.MainGrid.insert_selected_cols()
        event.Skip()
    
    def OnInsertTable(self, event): # wxGlade: MainWindow.<event_handler>
        """Insert one table into MainGrid and pysgrid """
        self.MainGrid.insert_selected_tables()
        event.GetString = lambda x=0: unicode(self.MainGrid.current_table)
        self.MainGrid.OnCombo(event)
        event.Skip()
    
    def OnDeleteRows(self, event): # wxGlade: MainWindow.<event_handler>
        """Deletes rows from all tables of the grid"""
        
        self.MainGrid.delete_selected_rows()
        event.Skip()
    
    def OnDeleteColumns(self, event): # wxGlade: MainWindow.<event_handler>
        """Deletes columnss from all tables of the grid"""
        
        self.MainGrid.delete_selected_cols()
        event.Skip()
    
    def OnDeleteTable(self, event): # wxGlade: MainWindow.<event_handler>
        """Deletes tables"""
        
        self.MainGrid.delete_selected_tables()
        
        newtable = max(0, min(self.MainGrid.current_table, \
                           self.MainGrid.pysgrid.sgrid.shape[2] - 1))
        
        event.GetString = lambda x=0: unicode(newtable)
        self.MainGrid.OnCombo(event)
        
        self.cbox_z.SetSelection(newtable)
        
        event.Skip()
    
    def OnResizeGrid(self, event):
        """Resizes current grid by appending/deleting rows, cols and tables"""
        
        dim_dialog = DimensionsEntryDialog(self)
        if dim_dialog.ShowModal() != wx.ID_OK:
            dim_dialog.Destroy()
            return False
        
        dim_dialog.Destroy()
        
        dimensions = tuple(dim_dialog.dimensions)
        
        # Check for each dimension, how many items are inserted or deleted
        dim_diff = [dimensions[i] - self.MainGrid.pysgrid.shape[i] \
                        for i in xrange(3)]
        
        for dim, diff in enumerate(dim_diff):
            self.MainGrid.change_dim(dim, diff)
        
        self.MainGrid.pysgrid.unredo.reset()
    
    def _getfilename(self, message, defaultDir=os.getcwd(), defaultFile="", \
                     wildcard=" Any file|*.*", style=wx.OPEN | wx.CHANGE_DIR):
        """Spawns a wx.FileDialog and returns filename"""
        
        filedlg = wx.FileDialog(self, message=message, defaultDir=defaultDir, \
                       defaultFile=defaultFile, wildcard=wildcard, style=style)
        if filedlg.ShowModal() == wx.ID_OK:
            path = filedlg.GetPath()
        else:
            path = None
        filedlg.Destroy()
        
        try:
            filename = os.path.split(path)[1]
        except AttributeError:
            return None
        
        return filename, filedlg.GetFilterIndex()
    
    def OnMacroList(self, event):
        """Invokes the MacroDialog and updates the macros in the app"""
        
        dlg = MacroDialog(None, -1, "", macros = self.MainGrid.pysgrid.macros)
        if dlg.ShowModal() == wx.ID_OK:
            # Insert function string into current cell
            targetcell = self.MainGrid.get_currentcell()
            macrostring = dlg.GetMacroString()
            try:
                self.MainGrid.entry_line.SetValue(macrostring)
            except TypeError:
                self.MainGrid.entry_line.SetValue("")
            if macrostring is not None:
                self.MainGrid.pysgrid[targetcell] = macrostring
                self.MainGrid.ForceRefresh()
        self.MainGrid.pysgrid.macros = dlg.macros
        self.MainGrid.pysgrid.set_global_macros(self.MainGrid.pysgrid.macros)
        dlg.Destroy()
        self.MainGrid.ForceRefresh()
    
    def OnMacroListLoad(self, event): # wxGlade: MainWindow.<event_handler>
        macrowildcard = " Macro file|*.*"
        # File choice
        filedlg = wx.FileDialog(
            self, message="Load a Macro-file", defaultDir=os.getcwd(),
            defaultFile="", wildcard=macrowildcard, \
            style=wx.OPEN | wx.CHANGE_DIR)
        if filedlg.ShowModal() == wx.ID_OK:
            path = filedlg.GetPath()
            filedlg.Destroy()
        macrocodes = {}
        infile = bz2.BZ2File(path, "r")
        macrocodes = pickle.load(infile)
        infile.close()
        #print macrocodes
        for macroname in macrocodes:
            self.MainGrid.pysgrid.macros.add(macrocodes[macroname])
        self.MainGrid.pysgrid.set_global_macros()
        event.Skip()
    
    def OnMacroListSave(self, event):
        """Event handler"""
        
        macrowildcard = " Macro file|*.*"
        # File choice
        filedlg = wx.FileDialog(
            self, message="Save a Macro-file", defaultDir=os.getcwd(),
            defaultFile="", wildcard=macrowildcard, \
            style=wx.OPEN | wx.CHANGE_DIR)
        if filedlg.ShowModal() == wx.ID_OK:
            path = filedlg.GetPath()
            filedlg.Destroy()
        macros = self.MainGrid.pysgrid.macros
        macrocodes = dict((m, macros[m].func_dict['macrocode']) for m in macros)
        
        bzip_dump(macrocodes, path)
        
        event.Skip()
    
    def OnFind(self, event): # wxGlade: MainWindow.<event_handler>
        """Find functionality should be in interfaces"""
        
        newstring = ""
        wx_map = { wx.wxEVT_COMMAND_FIND : "FIND",
                   wx.wxEVT_COMMAND_FIND_NEXT : "FIND_NEXT",
                   wx.wxEVT_COMMAND_FIND_REPLACE : "REPLACE",
                   wx.wxEVT_COMMAND_FIND_REPLACE_ALL : "REPLACE_ALL" }
        wx_flags = { 0: ["UP", ],
                     1: ["DOWN"],
                     2: ["UP", "WHOLE_WORD"],
                     3: ["DOWN", "WHOLE_WORD"],
                     4: ["UP", "MATCH_CASE"],
                     5: ["DOWN", "MATCH_CASE"],
                     6: ["UP", "WHOLE_WORD", "MATCH_CASE"],
                     7: ["DOWN", "WHOLE_WORD", "MATCH_CASE"] }
                     
        evt_type = event.GetEventType()
        evt_flags = event.GetFlags()
        
        try:
            event_type = wx_map[evt_type]
            event_flags = wx_flags[evt_flags]
        except KeyError:
            self.main_window_statusbar.SetStatusText("Unknown event type " + \
                "or flag:" + unicode(evt_type) + unicode(evt_flags))
            return 0
        event_find_string = event.GetFindString()
        event_replace_string = event.GetReplaceString()
        
        findpos = self.find_position(event_find_string, event_flags)
        
        if event_type in ["FIND", "FIND_NEXT", "REPLACE"]:
            self.find_gui_feedback(event, event_find_string, findpos)
        
        if event_type in ["REPLACE", "REPLACE_ALL"]:
            noreplaced = 0
            while findpos is not None:
                noreplaced += 1
                cellstring = self.MainGrid.pysgrid.sgrid[findpos]
                string_position = string_match(cellstring, \
                                    event_find_string, event_flags)
                newstring = cellstring[:string_position]
                newstring += cellstring[string_position:].replace(\
                                       event_find_string, \
                                       event_replace_string, 1)
                self.MainGrid.pysgrid[findpos] = newstring
                if event_type == "REPLACE":
                    self.main_window_statusbar.SetStatusText("'" +
                                 cellstring + "' replaced by '" + \
                                 newstring + "'.", 0)
                    break
                elif event_type == "REPLACE_ALL":
                    findpos = self.MainGrid.pysgrid.findnextmatch( \
                                 findpos, event_find_string, event_flags)
                else:
                    raise ValueError, "Event type " + event_type + " unknown."
            
            self.MainGrid.ForceRefresh()
            self.MainGrid.pysgrid.unredo.mark()
            
            if event_type == "REPLACE_ALL":
                self.main_window_statusbar.SetStatusText(unicode(noreplaced) + \
                                 " occurrences of '" + event_find_string + \
                                 "' replaced by '" +  event_replace_string + \
                                 "'.", 0)
            else:
                self.MainGrid.entry_line.SetValue(newstring)
        event.Skip()
    
    def find_position(self, event_find_string, event_flags):
        """Find position of event_find_string in MainGrid
        
        Parameters:
        -----------
        event_find_string: String
        \tString to find in grid
        event_flags: Int
        \twx.wxEVT_COMMAND_FIND flags
        
        """
        
        findfunc = self.MainGrid.pysgrid.findnextmatch
        
        # Search starts in next cell after the current one
        gridpos = list(self.MainGrid.key)
        if "DOWN" in event_flags:
            if gridpos[0] < self.MainGrid.shape[0]:
                gridpos[0] += 1
            elif gridpos[1] < self.MainGrid.shape[1]:
                gridpos[1] += 1
            elif gridpos[2] < self.MainGrid.shape[2]:
                gridpos[2] += 1
            else:
                gridpos = (0, 0, 0)
        elif "UP" in event_flags:
            if gridpos[0] > 0:
                gridpos[0] -= 1
            elif gridpos[1] > 0:
                gridpos[1] -= 1
            elif gridpos[2] > 0:
                gridpos[2] -= 1
            else:
                gridpos = [dim - 1 for dim in self.MainGrid.pysgrid.shape]
        gridpos = tuple(gridpos)
        return findfunc(gridpos, event_find_string, event_flags)
    
    def find_gui_feedback(self, event, event_find_string, findpos):
        """GUI feedback in find process
        
        * Grid cell selection
        * Status bar comments
        
        Parameters
        ----------
        findpos: 2-tuple of int
        \tPosition of found result in grid
        
        """
        if findpos is not None:
            self.MainGrid.selectnewcell(findpos, event)
            self.MainGrid.SelectBlock(findpos[0], findpos[1], 
                                      findpos[0], findpos[1])
            self.main_window_statusbar.SetStatusText("Found '" + \
                             event_find_string +  "' in cell " + \
                             unicode(list(findpos)) + ".", 0)
        else:
            self.main_window_statusbar.SetStatusText("'" + \
                             event_find_string + "' not found.", 0)
        
    def OnFindClose(self, event):
        """Refreshes the grid after closing the find dialog"""
        
        event.GetDialog().Destroy()
        self.main_window_statusbar.SetStatusText("", 0)
        self.MainGrid.ForceRefresh()
        event.Skip()
    
    def OnUndo(self, event):
        """Calls the gris undo method"""
        
        self.MainGrid.undo()
        event.Skip()
    
    def OnRedo(self, event):
        """Calls the gris redo method"""
        
        self.MainGrid.redo()
        event.Skip()
    
    def OnShowFind(self, event):
        """Calls the find dialog"""
        
        data = wx.FindReplaceData()
        dlg = wx.FindReplaceDialog(self, data, "Find")
        dlg.data = data  # save a reference to it...
        dlg.Show(True)
        event.Skip()
    
    def OnShowFindReplace(self, event):
        """Calls the find-replace dialog"""
        
        data = wx.FindReplaceData()
        dlg = wx.FindReplaceDialog(self, data, "Find & Replace", \
                                   wx.FR_REPLACEDIALOG)
        dlg.data = data  # save a reference to it...
        dlg.Show(True)
        event.Skip()
        
    def OnZoom(self, event):
        """Event handler for setting grid zoom via menu"""
        
        try:
            menuitem = event.GetEventObject().FindItemById(event.Id)
            menuitemtext = menuitem.GetText()
            self.MainGrid.zoom = int(menuitemtext[:-1]) / 100.0
        except AttributeError: 
            pass
        
        old_zoom = self.MainGrid.zoom
        
        if self.MainGrid.zoom < 1.0 and old_zoom > self.MainGrid.zoom + 0.1:
            old_zoom, self.MainGrid.zoom = \
                self.MainGrid.zoom, self.MainGrid.zoom + 0.1
            self.MainGrid.zoom_rows()
            self.MainGrid.zoom_cols()
            self.MainGrid.zoom_labels()
            
            self.MainGrid.ForceRefresh()            
            
            self.MainGrid.zoom = old_zoom
        
        self.MainGrid.zoom_rows()
        self.MainGrid.zoom_cols()
        self.MainGrid.zoom_labels()

        self.MainGrid.ForceRefresh()
        
        event.Skip()
    
# end of class MainWindow
