from pathlib import Path
import sys

import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore

class CreateGlobalToolbarCommand:
    wb_path: Path = Path(__file__).parent.parent

    def GetResources(self):
        return {
            'Pixmap': '',  # No icon
            'MenuText': 'Create Global Toolbar',
            'ToolTip': 'Create a toolbar with universal tools that appears in all workbenches'
        }

    def Activated(self):
        try:
            mw = FreeCADGui.getMainWindow()
            toolbar_name = "Detessellate_Global_Tools"

            # Check if toolbar already exists
            existing_toolbar = None
            for toolbar in mw.findChildren(QtGui.QToolBar):
                if toolbar.objectName() == toolbar_name:
                    existing_toolbar = toolbar
                    break

            if existing_toolbar:
                FreeCAD.Console.PrintMessage("Detessellate Global Tools toolbar already exists.\n")
                return

            # Create new toolbar
            custom_toolbar = QtGui.QToolBar("Detessellate Global", mw)
            custom_toolbar.setObjectName(toolbar_name)
            mw.addToolBar(QtCore.Qt.TopToolBarArea, custom_toolbar)

            # Add buttons - these tools work in any workbench
            self.add_coplanar_sketch_button(custom_toolbar)
            self.add_edgeloop_selector_button(custom_toolbar)
            self.add_varset_update_button(custom_toolbar)

            # No workbench toggle needed - always visible
            custom_toolbar.setVisible(True)

            FreeCAD.Console.PrintMessage("✓ Created 'Detessellate Global' toolbar.\n")
            FreeCAD.Console.PrintMessage("This toolbar is visible in all workbenches.\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating Global toolbar: {e}\n")
            import traceback
            traceback.print_exc()

    def add_coplanar_sketch_button(self, toolbar):
        """Add CoplanarSketch button"""
        try:
            macro_path = self.wb_path / "Macros" / "CoplanarSketch"
            icon_path = macro_path / "CoplanarSketch.svg"
            icon = QtGui.QIcon(str(icon_path))

            action = QtGui.QAction(icon, "Coplanar Sketch", toolbar)
            action.setToolTip("Create sketches coplanar to selected faces")
            action.triggered.connect(lambda: self.run_coplanar_sketch(macro_path))

            toolbar.addAction(action)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error adding CoplanarSketch button: {e}\n")

    def add_edgeloop_selector_button(self, toolbar):
        """Add EdgeLoopSelector button"""
        try:
            macro_path = self.wb_path / "Macros" / "EdgeLoopSelector"
            icon_path = macro_path / "EdgeLoopSelector.svg"
            icon = QtGui.QIcon(str(icon_path))

            action = QtGui.QAction(icon, "Edge Loop Selector", toolbar)
            action.setToolTip("Select connected edge loops")
            action.triggered.connect(lambda: self.run_edgeloop_selector(macro_path))

            toolbar.addAction(action)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error adding EdgeLoopSelector button: {e}\n")

    def add_varset_update_button(self, toolbar):
        """Add VarSetUpdate button"""
        try:
            macro_path = self.wb_path / "Macros" / "VarSet-Update"
            icon_path = macro_path / "VarSetUpdate.svg"
            icon = QtGui.QIcon(str(icon_path)) if icon_path.exists() else QtGui.QIcon()

            action = QtGui.QAction(icon, "VarSet Update", toolbar)
            action.setToolTip("Update variable sets in spreadsheet")
            action.triggered.connect(lambda: self.run_varset_update(macro_path))

            toolbar.addAction(action)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error adding VarSetUpdate button: {e}\n")

    def run_coplanar_sketch(self, macro_path: Path) -> None:
        """Directly run the CoplanarSketch macro"""
        try:
            if str(macro_path) not in sys.path:
                sys.path.append(str(macro_path))

            import importlib
            if 'CoplanarSketch' in sys.modules:
                import CoplanarSketch
                importlib.reload(CoplanarSketch)
            else:
                import CoplanarSketch

            # Macro creates dock widget on import

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error running CoplanarSketch: {e}\n")
            import traceback
            traceback.print_exc()

    def run_edgeloop_selector(self, macro_path: Path) -> None:
        """Directly run the EdgeLoopSelector macro"""
        try:
            if str(macro_path) not in sys.path:
                sys.path.append(str(macro_path))

            import importlib
            if 'EdgeLoopSelector' in sys.modules:
                import EdgeLoopSelector
                importlib.reload(EdgeLoopSelector)
            else:
                import EdgeLoopSelector

            # Call appropriate function - adjust once you share the macro

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error running EdgeLoopSelector: {e}\n")
            import traceback
            traceback.print_exc()

    def run_varset_update(self, macro_path: Path) -> None:
        """Directly run the VarSetUpdate macro"""
        try:
            if str(macro_path) not in sys.path:
                sys.path.append(str(macro_path))

            import importlib
            if 'VarSetUpdate' in sys.modules:
                import VarSetUpdate
                importlib.reload(VarSetUpdate)
            else:
                import VarSetUpdate

            # Call appropriate function - adjust once you share the macro

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error running VarSetUpdate: {e}\n")
            import traceback
            traceback.print_exc()

    def IsActive(self):
        return True
