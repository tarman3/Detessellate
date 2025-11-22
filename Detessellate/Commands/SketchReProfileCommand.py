import os, sys
import FreeCAD
import FreeCADGui

class SketchReProfileCommand:
    def GetResources(self):
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "Macros", "SketchReProfile", "sketchreprofile.svg"
        )
        return {
            'Pixmap': icon_path,
            'MenuText': 'Sketch ReProfile',
            'ToolTip': 'Reprocess sketch profiles'
        }

    def Activated(self):
        macro_path = os.path.join(os.path.dirname(__file__), "..", "Macros", "SketchReProfile")
        macro_path = os.path.abspath(macro_path)
        if macro_path not in sys.path:
            sys.path.append(macro_path)

        try:
            import importlib
            if 'SketchReProfile' in sys.modules:
                import SketchReProfile
                importlib.reload(SketchReProfile)
            else:
                import SketchReProfile

            # Call the appropriate function based on the macro

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error running SketchReProfile: {e}\n")
            import traceback
            traceback.print_exc()

    def IsActive(self):
        # Active when a sketch is being edited
        return FreeCADGui.activeDocument() is not None and FreeCADGui.ActiveDocument.getInEdit() is not None
