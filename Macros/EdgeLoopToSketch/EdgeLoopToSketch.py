import FreeCAD
import FreeCADGui
import Part
import Sketcher
from PySide.QtWidgets import QInputDialog, QMessageBox

def edge_loop_to_sketch():
    """
    Creates a parametric sketch from selected edges, preserving curve types.
    Expects edges to already be selected (e.g., via EdgeLoopSelector).
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        FreeCAD.Console.PrintError("Error: No active document.\n")
        return

    selection = FreeCADGui.Selection.getSelectionEx()
    if not selection:
        FreeCAD.Console.PrintError("Error: No edges selected.\n")
        return

    # Collect selected edges
    obj = selection[0].Object
    selected_edges = []
    
    for sel_ex in selection:
        if sel_ex.Object.Name != obj.Name:
            FreeCAD.Console.PrintError("Error: All edges must be from the same object.\n")
            return
        for sub_name in sel_ex.SubElementNames:
            if sub_name.startswith("Edge"):
                edge_idx = int(sub_name[4:]) - 1
                selected_edges.append(obj.Shape.Edges[edge_idx])

    if not selected_edges:
        FreeCAD.Console.PrintError("Error: No valid edges selected.\n")
        return

    doc.openTransaction("Create Sketch from Edge Loop")
    
    try:
        tolerance = 1e-6
        plane_point = None
        plane_normal = None
        
        # Special case: single edge that defines its own plane
        if len(selected_edges) == 1:
            edge = selected_edges[0]
            curve_type = type(edge.Curve).__name__
            
            if curve_type == 'Circle':
                # Circle defines its own plane via its axis
                circle = edge.Curve
                plane_normal = circle.Axis.normalize()
                plane_point = circle.Center
                FreeCAD.Console.PrintMessage("Using plane from circle geometry.\n")
            elif curve_type == 'BSplineCurve':
                # Check if B-spline is planar by examining control points
                bspline = edge.Curve
                poles = bspline.getPoles()
                
                if len(poles) < 3:
                    raise Exception("B-spline does not have enough control points to define a plane.")
                
                # Find 3 non-collinear poles to define plane
                plane_point = poles[0]
                
                for i in range(1, len(poles)):
                    v1 = poles[i] - plane_point
                    for j in range(i + 1, len(poles)):
                        v2 = poles[j] - plane_point
                        cross = v1.cross(v2)
                        if cross.Length > tolerance:
                            plane_normal = cross.normalize()
                            break
                    if plane_normal:
                        break
                
                if not plane_normal:
                    raise Exception("B-spline control points are collinear and cannot define a plane.")
                
                # Verify all poles are coplanar
                for pole in poles:
                    distance = abs((pole - plane_point).dot(plane_normal))
                    if distance > tolerance:
                        raise Exception("B-spline is non-planar (3D curve). Select additional edges to define the plane.")
                
                FreeCAD.Console.PrintMessage("Using plane from planar B-spline geometry.\n")
            else:
                raise Exception(f"Single edge of type '{curve_type}' cannot define a plane. Select at least 2 edges.")
        
        # Multiple edges: validate coplanarity
        if len(selected_edges) >= 2:
            unique_points = []
            all_points = []
            
            for edge in selected_edges:
                for vertex in edge.Vertexes:
                    pt = vertex.Point
                    all_points.append(pt)
                    if not any(pt.isEqual(existing, tolerance) for existing in unique_points):
                        unique_points.append(pt)

            if len(unique_points) < 3:
                raise Exception("Selected edges do not provide enough unique points to define a plane.")

            # Find 3 non-collinear points to define plane
            plane_point = unique_points[0]
            
            for i in range(1, len(unique_points)):
                v1 = unique_points[i] - plane_point
                for j in range(i + 1, len(unique_points)):
                    v2 = unique_points[j] - plane_point
                    cross = v1.cross(v2)
                    if cross.Length > tolerance:
                        plane_normal = cross.normalize()
                        break
                if plane_normal:
                    break

            if not plane_normal:
                raise Exception("Selected edges are collinear and cannot define a plane.")

            # Verify all points are coplanar
            for pt in all_points:
                distance = abs((pt - plane_point).dot(plane_normal))
                if distance > tolerance:
                    raise Exception("Selected edges are not coplanar.")

        # Calculate placement
        if len(selected_edges) == 1:
            # For single circle, use its center
            center = plane_point
        else:
            # For multiple edges, use centroid of all points
            center = sum(all_points, FreeCAD.Vector()).multiply(1.0 / len(all_points))
        
        placement = create_sketch_placement(plane_normal, center)

        # Show destination dialog
        choice = show_destination_dialog()
        if not choice:
            doc.abortTransaction()
            FreeCAD.Console.PrintMessage("Sketch creation cancelled.\n")
            return

        # Create sketch based on destination choice
        if choice["type"] == "standalone":
            sketch = create_standalone_sketch(doc, placement, selected_edges)
        elif choice["type"] == "new_body":
            body = doc.addObject("PartDesign::Body", "Body")
            sketch = create_body_sketch(doc, body, placement, selected_edges)
        elif choice["type"] == "existing_body":
            body = doc.getObject(choice["body_name"])
            if not body:
                raise Exception(f"Body {choice['body_name']} not found.")
            sketch = create_body_sketch(doc, body, placement, selected_edges)

        doc.recompute()
        
        # Select the new sketch and fit view
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(sketch)
        FreeCADGui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.activeDocument().activeView().fitAll()

        doc.commitTransaction()
        FreeCAD.Console.PrintMessage(f"Sketch created successfully with {len(selected_edges)} edges.\n")

    except Exception as e:
        doc.abortTransaction()
        FreeCAD.Console.PrintError(f"Sketch creation failed: {e}\n")
        QMessageBox.critical(None, "Error", f"Sketch creation failed:\n{str(e)}")


def create_sketch_placement(normal, center):
    """Create placement for sketch from normal and center point."""
    normal = normal.normalize() if normal.Length > 1e-6 else FreeCAD.Vector(0, 0, 1)
    z_axis = FreeCAD.Vector(0, 0, 1)
    
    if abs(normal.dot(z_axis)) > 0.999:
        rotation = FreeCAD.Rotation() if normal.z > 0 else FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 180)
    else:
        rotation = FreeCAD.Rotation(z_axis, normal)
    
    return FreeCAD.Placement(center, rotation)


def show_destination_dialog():
    """Show dialog for sketch destination choice."""
    doc = FreeCAD.ActiveDocument
    body_names = [o.Name for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
    options = ["<Standalone (Part Workbench)>", "<Create New Body (PartDesign)>"] + body_names

    item, ok = QInputDialog.getItem(
        FreeCADGui.getMainWindow(),
        "Sketch Destination",
        "Choose where to create the sketch:",
        options, 0, False
    )

    if not ok or not item:
        return None

    if item == "<Standalone (Part Workbench)>":
        return {"type": "standalone"}
    elif item == "<Create New Body (PartDesign)>":
        return {"type": "new_body"}
    else:
        return {"type": "existing_body", "body_name": item}


def create_standalone_sketch(doc, placement, edges):
    """Create standalone sketch in Part workbench."""
    sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
    sketch.Placement = placement
    
    inverse_placement = sketch.getGlobalPlacement().inverse()
    add_geometry_to_sketch(sketch, edges, inverse_placement)
    
    return sketch


def create_body_sketch(doc, body, placement, edges):
    """Create sketch attached to PartDesign body."""
    sketch = doc.addObject("Sketcher::SketchObject", "Sketch")
    
    # Add sketch to body
    body.ViewObject.dropObject(sketch, None, '', [])
    
    # Set up attachment to body origin
    sketch.AttachmentSupport = [(body.Origin.OriginFeatures[0], '')]
    sketch.MapMode = 'ObjectXY'
    sketch.AttachmentOffset.Base = placement.Base
    sketch.AttachmentOffset.Rotation = placement.Rotation
    sketch.Placement = FreeCAD.Placement()
    
    doc.recompute()  # Resolve attachment before adding geometry
    
    inverse_placement = sketch.getGlobalPlacement().inverse()
    add_geometry_to_sketch(sketch, edges, inverse_placement)
    
    return sketch


def add_geometry_to_sketch(sketch, edges, inverse_placement):
    """Add geometry to sketch, preserving curve types."""
    tolerance = 0.001
    edge_map = {}  # For coincident constraints
    
    for edge in edges:
        try:
            curve_type = type(edge.Curve).__name__
            
            if curve_type == 'Line':
                add_line_to_sketch(sketch, edge, inverse_placement, edge_map)
            elif curve_type == 'Circle':
                add_circle_to_sketch(sketch, edge, inverse_placement, edge_map)
            elif curve_type == 'BSplineCurve':
                add_bspline_to_sketch(sketch, edge, inverse_placement, edge_map)
            else:
                FreeCAD.Console.PrintWarning(f"Unsupported curve type: {curve_type}, converting to line.\n")
                add_line_to_sketch(sketch, edge, inverse_placement, edge_map)
                
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Failed to add edge: {e}\n")
    
    # Add coincident constraints
    add_coincident_constraints(sketch, edge_map)


def add_line_to_sketch(sketch, edge, inverse_placement, edge_map):
    """Add a line segment to sketch."""
    v_start = inverse_placement.multVec(edge.Vertexes[0].Point)
    v_end = inverse_placement.multVec(edge.Vertexes[-1].Point)
    
    geo_index = sketch.addGeometry(Part.LineSegment(v_start, v_end), False)
    
    # Update edge map for constraints
    update_edge_map(edge_map, edge.Vertexes[0].Point, geo_index, 1)
    update_edge_map(edge_map, edge.Vertexes[-1].Point, geo_index, 2)


def add_circle_to_sketch(sketch, edge, inverse_placement, edge_map):
    """Add a circle or arc to sketch."""
    circle = edge.Curve
    center_local = inverse_placement.multVec(circle.Center)
    
    # Check if it's a full circle or an arc
    # Full circle if arc length is close to 2*pi*r
    arc_length = edge.Length
    full_circle_length = 2 * 3.141592653589793 * circle.Radius
    
    if abs(arc_length - full_circle_length) < 0.01:
        # Full circle
        geo_index = sketch.addGeometry(Part.Circle(center_local, FreeCAD.Vector(0, 0, 1), circle.Radius), False)
    else:
        # Arc - use 3 points
        v_start = inverse_placement.multVec(edge.Vertexes[0].Point)
        v_end = inverse_placement.multVec(edge.Vertexes[-1].Point)
        
        # Get midpoint on arc
        param_range = edge.ParameterRange
        mid_param = (param_range[0] + param_range[1]) / 2
        mid_point_global = edge.valueAt(mid_param)
        v_mid = inverse_placement.multVec(mid_point_global)
        
        geo_index = sketch.addGeometry(Part.ArcOfCircle(v_start, v_mid, v_end), False)
        
        # Update edge map for arc endpoints
        update_edge_map(edge_map, edge.Vertexes[0].Point, geo_index, 1)
        update_edge_map(edge_map, edge.Vertexes[-1].Point, geo_index, 2)


def add_bspline_to_sketch(sketch, edge, inverse_placement, edge_map):
    """Add a B-spline to sketch."""
    bspline = edge.Curve
    
    # Get control points (poles)
    poles = bspline.getPoles()
    poles_local = [inverse_placement.multVec(p) for p in poles]
    
    # Get knots and multiplicities
    knots = bspline.getKnots()
    mults = bspline.getMultiplicities()
    degree = bspline.Degree
    periodic = bspline.isPeriodic()
    
    # Create B-spline curve
    bspline_local = Part.BSplineCurve()
    bspline_local.buildFromPolesMultsKnots(
        poles_local,
        mults,
        knots,
        periodic,
        degree
    )
    
    geo_index = sketch.addGeometry(bspline_local, False)
    
    # Update edge map for B-spline endpoints
    update_edge_map(edge_map, edge.Vertexes[0].Point, geo_index, 1)
    update_edge_map(edge_map, edge.Vertexes[-1].Point, geo_index, 2)


def update_edge_map(edge_map, point, geo_index, vertex_id):
    """Update edge map for coincident constraint tracking."""
    key = (round(point.x, 5), round(point.y, 5), round(point.z, 5))
    edge_map.setdefault(key, []).append((geo_index, vertex_id))


def add_coincident_constraints(sketch, edge_map):
    """Add coincident constraints at shared vertices."""
    constraint_count = 0
    
    for group in edge_map.values():
        if len(group) > 1:
            # Connect first to second only (avoid constraint explosion)
            base = group[0]
            other = group[1]
            try:
                sketch.addConstraint(Sketcher.Constraint('Coincident', base[0], base[1], other[0], other[1]))
                constraint_count += 1
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Constraint failed: {e}\n")
    
    FreeCAD.Console.PrintMessage(f"Added {constraint_count} coincident constraints.\n")


# Run the macro
edge_loop_to_sketch()