import os, sys
import FreeCAD
import FreeCADGui

class VarSetUpdateCommand:
    def GetResources(self):
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "Macros", "VarSet-Update", "varsetupdate.svg"
        )
        return {
            'Pixmap': icon_path if os.path.exists(icon_path) else '',  # Empty string = text button fallback
            'MenuText': 'VarSet Update',
            'ToolTip': 'Update VarSet Properties'
        }

    def Activated(self):
        macro_path = os.path.join(os.path.dirname(__file__), "..", "Macros", "VarSet-Update")
        macro_path = os.path.abspath(macro_path)
        if macro_path not in sys.path:
            sys.path.append(macro_path)

        try:
            import importlib
            if 'VarSetUpdate' in sys.modules:  # Note: Python converts hyphens to underscores in module names
                import VarSetUpdate
                importlib.reload(VarSetUpdate)
            else:
                import VarSetUpdate

            # The macro will execute on import or call the appropriate function
            # Adjust based on how VarSetUpdate.py is structured

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error running VarSet Update: {e}\n")
            import traceback
            traceback.print_exc()

    def IsActive(self):
        return True  # Adjust if it needs specific conditions
