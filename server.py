#!/usr/bin/env python3
"""
CPLEX Optimization MCP Server
Provides optimization tools using IBM CPLEX (docplex) and CPLEX OPL Studio
"""
import json
import subprocess
import tempfile
import os
from typing import Any
from pathlib import Path
from fastmcp import FastMCP

# Try to import CPLEX
try:
    from docplex.mp.model import Model as CPLEXModel
    CPLEX_AVAILABLE = True
except ImportError:
    CPLEX_AVAILABLE = False
    raise ImportError("CPLEX (docplex) is not available. Please install: pip install docplex")

# CPLEX OPL Studio path
CPLEX_OPLRUN = "/Applications/CPLEX_Studio2211/opl/bin/arm64_osx/oplrun"
CPLEX_OPL_AVAILABLE = os.path.exists(CPLEX_OPLRUN)

# Initialize FastMCP Server
mcp = FastMCP("cplex-optimizer")


class OptimizationSolver:
    """Optimization solver using CPLEX (docplex)"""
    
    def __init__(self):
        self.solver_name = "CPLEX (docplex)"
    
    def solve_production_planning(
        self,
        products: list[str],
        profit: dict[str, float],
        labor_hours: dict[str, float],
        material_kg: dict[str, float],
        max_labor: float,
        max_material: float,
        min_production: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Solve production planning using CPLEX (docplex)"""
        mdl = CPLEXModel(name='Production_Planning')
        
        # Decision variables
        production = {p: mdl.continuous_var(name=f'production_{p}', lb=0) for p in products}
        
        # Objective: Maximize profit
        mdl.maximize(mdl.sum(profit[p] * production[p] for p in products))
        
        # Constraints
        mdl.add_constraint(
            mdl.sum(labor_hours[p] * production[p] for p in products) <= max_labor,
            'labor_constraint'
        )
        mdl.add_constraint(
            mdl.sum(material_kg[p] * production[p] for p in products) <= max_material,
            'material_constraint'
        )
        
        if min_production:
            for p in products:
                if p in min_production:
                    mdl.add_constraint(production[p] >= min_production[p], f'min_prod_{p}')
        
        # Solve
        solution = mdl.solve()
        
        if solution:
            return {
                "status": "Optimal",
                "optimal": True,
                "solver": "CPLEX",
                "objective_value": solution.objective_value,
                "production_plan": {p: production[p].solution_value for p in products},
                "resource_usage": {
                    "labor_hours": sum(labor_hours[p] * production[p].solution_value for p in products),
                    "material_kg": sum(material_kg[p] * production[p].solution_value for p in products)
                },
                "resource_utilization": {
                    "labor": sum(labor_hours[p] * production[p].solution_value for p in products) / max_labor * 100 if max_labor > 0 else 0,
                    "material": sum(material_kg[p] * production[p].solution_value for p in products) / max_material * 100 if max_material > 0 else 0
                }
            }
        else:
            return {
                "status": "Infeasible",
                "optimal": False,
                "solver": "CPLEX",
                "objective_value": None,
                "production_plan": {},
                "resource_usage": {},
                "resource_utilization": {}
            }


solver = OptimizationSolver()


@mcp.tool()
def get_solver_info() -> str:
    """
    Get information about available optimization solvers.
    
    Returns:
        JSON string with solver information
    """
    info = {
        "cplex_available": CPLEX_AVAILABLE,
        "opl_available": CPLEX_OPL_AVAILABLE,
        "active_solver": solver.solver_name,
        "opl_path": CPLEX_OPLRUN if CPLEX_OPL_AVAILABLE else None,
        "description": "CPLEX is IBM's commercial optimization solver. Supports docplex (Python API) and OPL Studio (.mod/.dat files)."
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def solve_production_planning(
    products: list[str],
    profit: dict[str, float],
    labor_hours: dict[str, float],
    material_kg: dict[str, float],
    max_labor: float,
    max_material: float,
    min_production: dict[str, float] | None = None
) -> str:
    """
    Solve production planning optimization problem using CPLEX. Maximizes profit subject to resource constraints.
    
    Args:
        products: List of product names
        profit: Profit per unit for each product (e.g., {'Product_A': 40, 'Product_B': 30})
        labor_hours: Labor hours required per unit for each product
        material_kg: Material (kg) required per unit for each product
        max_labor: Maximum available labor hours
        max_material: Maximum available material (kg)
        min_production: Optional: Minimum production quantity for each product
    
    Returns:
        JSON string with optimization results
    """
    try:
        result = solver.solve_production_planning(
            products=products,
            profit=profit,
            labor_hours=labor_hours,
            material_kg=material_kg,
            max_labor=max_labor,
            max_material=max_material,
            min_production=min_production
        )
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e), "solver": solver.solver_name}, indent=2)


@mcp.tool()
def solve_simple_lp(
    objective_coeffs: dict[str, float],
    constraints: list[dict[str, Any]],
    maximize: bool = True
) -> str:
    """
    Solve a simple linear programming problem using CPLEX.
    
    Args:
        objective_coeffs: Coefficients for objective function (e.g., {'x': 3, 'y': 2})
        constraints: List of constraints, each with 'coeffs', 'sense' ('<=', '>=', '='), and 'rhs'
                    Example: [{'coeffs': {'x': 1, 'y': 2}, 'sense': '<=', 'rhs': 10}]
        maximize: True to maximize, False to minimize
    
    Returns:
        JSON string with optimization results
    """
    try:
        mdl = CPLEXModel(name='Simple_LP')
        
        # Create variables
        vars_dict = {var: mdl.continuous_var(name=var, lb=0) for var in objective_coeffs.keys()}
        
        # Objective
        obj_expr = mdl.sum(objective_coeffs[var] * vars_dict[var] for var in objective_coeffs.keys())
        if maximize:
            mdl.maximize(obj_expr)
        else:
            mdl.minimize(obj_expr)
        
        # Constraints
        for i, constraint in enumerate(constraints):
            coeffs = constraint['coeffs']
            sense = constraint['sense']
            rhs = constraint['rhs']
            
            lhs = mdl.sum(coeffs.get(var, 0) * vars_dict[var] for var in vars_dict.keys())
            
            if sense == '<=':
                mdl.add_constraint(lhs <= rhs, f'constraint_{i}')
            elif sense == '>=':
                mdl.add_constraint(lhs >= rhs, f'constraint_{i}')
            elif sense == '=':
                mdl.add_constraint(lhs == rhs, f'constraint_{i}')
        
        solution = mdl.solve()
        
        if solution:
            return json.dumps({
                "status": "Optimal",
                "solver": "CPLEX",
                "objective_value": solution.objective_value,
                "variables": {var: vars_dict[var].solution_value for var in vars_dict.keys()}
            }, indent=2)
        else:
            return json.dumps({"status": "Infeasible", "solver": "CPLEX"}, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e), "solver": "CPLEX"}, indent=2)


@mcp.tool()
def run_opl_model(
    mod_content: str,
    dat_content: str | None = None
) -> str:
    """
    Run CPLEX OPL model (.mod file) with optional data file (.dat).
    This directly executes CPLEX IDE's oplrun command.
    
    Args:
        mod_content: Content of the .mod file (OPL model)
        dat_content: Optional content of the .dat file (data)
    
    Returns:
        JSON string with execution results
    """
    if not CPLEX_OPL_AVAILABLE:
        return json.dumps({
            "error": "CPLEX OPL Studio not found",
            "oplrun_path": CPLEX_OPLRUN,
            "suggestion": "Install CPLEX Studio or use docplex tools instead"
        }, indent=2)
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            mod_path = Path(tmpdir) / "model.mod"
            dat_path = Path(tmpdir) / "model.dat" if dat_content else None
            
            # Write model file
            mod_path.write_text(mod_content)
            
            # Write data file if provided
            if dat_content and dat_path:
                dat_path.write_text(dat_content)
            
            # Run oplrun
            cmd = [CPLEX_OPLRUN, str(mod_path)]
            if dat_path:
                cmd.append(str(dat_path))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            return json.dumps({
                "status": "success" if result.returncode == 0 else "error",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "solver": "CPLEX OPL Studio",
                "oplrun_path": CPLEX_OPLRUN
            }, indent=2)
    
    except subprocess.TimeoutExpired:
        return json.dumps({
            "error": "Execution timeout (5 minutes)",
            "solver": "CPLEX OPL Studio"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "solver": "CPLEX OPL Studio"
        }, indent=2)


@mcp.tool()
def run_opl_from_files(
    mod_file_path: str,
    dat_file_path: str | None = None
) -> str:
    """
    Run CPLEX OPL model from existing .mod and .dat files.
    
    Args:
        mod_file_path: Path to the .mod file
        dat_file_path: Optional path to the .dat file
    
    Returns:
        JSON string with execution results
    """
    if not CPLEX_OPL_AVAILABLE:
        return json.dumps({
            "error": "CPLEX OPL Studio not found",
            "oplrun_path": CPLEX_OPLRUN
        }, indent=2)
    
    try:
        # Check if files exist
        if not os.path.exists(mod_file_path):
            return json.dumps({"error": f"Model file not found: {mod_file_path}"}, indent=2)
        
        if dat_file_path and not os.path.exists(dat_file_path):
            return json.dumps({"error": f"Data file not found: {dat_file_path}"}, indent=2)
        
        # Run oplrun
        cmd = [CPLEX_OPLRUN, mod_file_path]
        if dat_file_path:
            cmd.append(dat_file_path)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return json.dumps({
            "status": "success" if result.returncode == 0 else "error",
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "solver": "CPLEX OPL Studio",
            "mod_file": mod_file_path,
            "dat_file": dat_file_path
        }, indent=2)
    
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Execution timeout (5 minutes)"}, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "solver": "CPLEX OPL Studio"
        }, indent=2)

# Made with Bob
