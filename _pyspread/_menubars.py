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
_menubars
===========

Provides menubars

Provides:
---------
  1. ContextMenu: Context menu for main grid
  2. MainMenu: Main menu of pyspread

"""
import wx

class _filledMenu(wx.Menu):
    """Menu that fills from the attribute menudata.

    Parameters:
    parent: object
    \tThe parent object that hosts the event handler methods
    menubar: wx.Menubar, defaults to parent
    \tThe menubar to which the menu is attached

    menudata has the following structure:
    [
        [wx.Menu, "Menuname", [\
            [wx.MenuItem, ["Methodname", "Itemlabel", "Help"]] , \
            ...
            "Separator" , \
            ...
            [wx.Menu, ...], \
            ...
        ] , \
    ...
    ]
    """

    menudata = []

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop('parent')
        try:
            self.menubar = kwargs.pop('menubar')
        except KeyError:
            self.menubar = self.parent
        wx.Menu.__init__(self, *args, **kwargs)
        
        # Menu methodname - item storage
        self.methodname_item = {}
        
        self._add_submenu(self, self.menudata)

    def _add_submenu(self, parent, data):
        """Adds items in data as a submenu to parent"""

        for item in data:
            obj = item[0]
            if obj == wx.Menu:
                menuname = item[1]
                submenu = item[2]
                menu = obj()
                self._add_submenu(menu, submenu)
                if parent == self:
                    self.menubar.Append(menu, menuname)
                else:
                    parent.AppendMenu(wx.NewId(), menuname, menu)
            elif obj == wx.MenuItem:
                methodname = item[1][0]
                
                method = self.parent.__getattribute__(methodname)
                if len(item) == 3:
                    style = item[2]
                else:
                    style = wx.ITEM_NORMAL
                
                item_id = wx.NewId()
                
                params = [parent, item_id] + item[1][1:] + [style]
                
                menuitem = obj(*params)
                parent.AppendItem(menuitem)
                
                self.methodname_item[methodname] = menuitem
                
                self.parent.Bind(wx.EVT_MENU, method, menuitem)
                
            elif obj == "Separator":
                parent.AppendSeparator()
                
            else:
                raise TypeError, "Menu item unknown"

# end of class _filledMenu


class ContextMenu(_filledMenu):
    """Context menu for grid operations"""

    item = wx.MenuItem
    menudata = [ \
    [item, ["OnCut", "Cu&t\tCtrl+x", "Cut cell to clipboard"]], \
    [item, ["OnCopy", "&Copy\tCtrl+c", "Copy input strings to clipboard"]], \
    [item, ["OnPaste", "&Paste\tCtrl+v", "Paste cell from clipboard"]], \
    [item, ["OnInsertRows", "Insert &rows\tShift+Ctrl+i", 
        "Insert rows at cursor"]], \
    [item, ["OnInsertColumns", "&Insert columns\tCtrl+i", 
        "Insert columns at cursor"]], \
    [item, ["OnDeleteRows", "Delete rows\tShift+Ctrl+d", "Delete rows" ]], \
    [item, ["OnDeleteColumns", "Delete columns\tCtrl+Alt+d", "Delete columns"]]]


# end of class ContextMenu


class MainMenu(_filledMenu):
    """Main application menu"""
    item = wx.MenuItem
    menudata = [ \
        [wx.Menu, "&File", [\
            [item, ["OnFileNew", "&New\tCtrl+n", 
                "Create a new, empty spreadsheet"]], \
            [item, ["OnFileOpen", "&Open\tCtrl+o", 
                "Open spreadsheet from file"]], \
            [item, ["OnFileSave", "&Save\tCtrl+s", "Save spreadsheet"]], \
            [item, ["OnFileSaveAs", "Save &As\tShift+Ctrl+s", 
                "Save spreadsheet to a new file"]], \
            ["Separator"], \
            [item, ["OnFileImport", "&Import", "Import a file " + \
                "(Supported formats: CSV, Tab separated text)"]], \
            [item, ["OnFileExport", "&Export", 
                "Export a file (Supported formats: CSV)"]], \
            ["Separator"], \
            [item, ["OnFileApprove", "&Approve file", 
                "Approve, unfreeze and sign the curretn file"]], \
            ["Separator"], \
            [item, ["OnFilePrint", "&Print...\tCtrl+p", 
                "Print current spreadsheet"]], \
            ["Separator"], \
            [item, ["OnExit", "E&xit\tCtrl+q", "Exit Program"]]] \
        ], \
        [wx.Menu, "&Edit", [\
            [item, ["OnUndo", "&Undo\tCtrl+z", "Undo last step"]], \
            [item, ["OnRedo", "&Redo\tShift+Ctrl+z", 
                "Redo last undone step"]], \
            ["Separator"], \
            [item, ["OnCut", "Cu&t\tCtrl+x", "Cut cell to clipboard"]], \
            [item, ["OnCopy", "&Copy\tCtrl+c", 
                "Copy the input strings of the cells to clipboard"]], \
            [item, ["OnCopyResult", "Copy &Results\tShift+Ctrl+c", 
                "Copy the result strings of the cells to the clipboard"]], \
            [item, ["OnPaste", "&Paste\tCtrl+v", 
                "Paste cells from clipboard"]], \
            ["Separator"], \
            [item, ["OnShowFind", "&Find\tCtrl+f", "Find cell by content"]], \
            [item, ["OnShowFindReplace", "Replace\tCtrl+Shift+f", 
                "Replace strings in cells"]], \
            ["Separator"], \
            [item, ["OnInsertRows", "Insert &rows\tShift+Ctrl+i", 
                "Insert rows at cursor"]], \
            [item, ["OnInsertColumns", "&Insert columns\tCtrl+i", 
                "Insert columns at cursor"]], \
            [item, ["OnInsertTable", "Insert &table", 
                "Insert table before current table"]], \
            ["Separator"], \
            [item, ["OnDeleteRows", "Delete rows\tShift+Ctrl+d", 
                "Delete rows"]], \
            [item, ["OnDeleteColumns", "Delete columns\tCtrl+Alt+d", 
                "Delete columns"]], \
            [item, ["OnDeleteTable", "Delete table", 
                "Delete current table"]], \
            ["Separator"], \
            [item, ["OnResizeGrid", "Resize grid", "Resize the grid. " + \
                    "The buttom right lowermost cells are deleted first."]]] \
        ], \
        [wx.Menu, "&View", [ \
            [wx.Menu, "Zoom", [ \
                [item, ["OnZoom", str(int(zoom)) + "%", 
                        "Zoom " + str(int(zoom)) + "%"] \
                ] for zoom in xrange(50, 350, 10)]
                ] \
            ], \
        ], \
        [wx.Menu, "&Macro", [\
            [item, ["OnMacroList", "&Macro list\tCtrl+m", 
                        "Choose, fill in, manage, and create macros"]], \
            [item, ["OnMacroListLoad", "&Load macro list\tShift+Ctrl+m", 
                        "Load macro list"]], \
            [item, ["OnMacroListSave", "&Save macro list\tShift+Alt+m", 
                        "Save macro list"]]]], \
        [wx.Menu, "&Help", [\
            [item, ["OnManual", "&Manual", "Launch manual"]],
            [item, ["OnTutorial", "&Tutorial", "Launch tutorial"]],
            [item, ["OnFAQ", "&FAQ", "Launch frequently asked questions"]],
            ["Separator"], \
            [item, ["OnAbout", "&About", "About this program"]],
            ] \
        ] \
    ]

# end of class MainMenu
