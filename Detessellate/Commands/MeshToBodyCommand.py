import os, sys
import FreeCAD
import FreeCADGui

class MeshToBodyCommand:
    def GetResources(self):
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "Macros", "MeshToBody", "meshtobody.svg"
        )
        return {
            'Pixmap': icon_path,
            'MenuText': 'Mesh To Body',
            'ToolTip': 'Convert mesh to parametric body'
        }

    def Activated(self):
        macro_path = os.path.join(os.path.dirname(__file__), "..", "Macros", "MeshToBody")
        macro_path = os.path.abspath(macro_path)
        if macro_path not in sys.path:
            sys.path.append(macro_path)

        try:
            import MeshToBody
            if hasattr(MeshToBody, "run"):
                MeshToBody.run()
            else:
                FreeCAD.Console.PrintMessage("MeshToBody macro imported, but no run() function found.\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error running MeshToBody: {e}\n")

    def IsActive(self):
        return True
