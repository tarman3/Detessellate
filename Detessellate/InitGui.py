import FreeCADGui
import traceback
import sys

print("Detessellate InitGui.py starting to load")

# Import at module level and make it globally accessible
MeshPlacementCommand = None

try:
    from Commands.MeshPlacementCommand import MeshPlacementCommand
    print("MeshPlacementCommand imported successfully")
except Exception as e:
    print(f"ERROR importing MeshPlacementCommand: {e}")
    traceback.print_exc()

print("Detessellate InitGui.py loaded")

class DetessellateWorkbench(FreeCADGui.Workbench):
    MenuText = "Detessellate"
    ToolTip = "Tools to reverse engineer meshes"
    Icon = "Detessellate/Macros/MeshPlacement/meshplacement.svg"  # placeholder icon

    def Initialize(self):
        # Access the global MeshPlacementCommand
        global MeshPlacementCommand

        # Only register command if import was successful
        if MeshPlacementCommand is not None:
            FreeCADGui.addCommand('MeshPlacement', MeshPlacementCommand())

            # --- Toolbars ---
            self.appendToolbar("Detessellate Mesh", ['MeshPlacement'])

            # --- Unified Menu with sections ---
            self.appendMenu("Detessellate", ['MeshPlacement'])
        else:
            print("Skipping MeshPlacement registration due to import error")

        # Empty toolbars for future use
        self.appendToolbar("Detessellate Solid", [])
        self.appendToolbar("Detessellate Utilities", [])

        # Empty menu sections for future use
        self.appendMenu("Detessellate", [])
        self.appendMenu("Detessellate", [])

    def Activated(self):
        pass

    def Deactivated(self):
        pass

FreeCADGui.addWorkbench(DetessellateWorkbench())
