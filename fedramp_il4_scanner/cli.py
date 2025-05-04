import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fedramp_il4_scanner.audit import AuditLogger
from fedramp_il4_scanner.scanner import IL4Scanner

app = typer.Typer(help="FedRAMP Moderate to DoD IL4 Gap Scanner")
console = Console()

# Store the exit code to be used by the CLI
exit_code = 0

def set_exit_code(code: int):
    """Set the exit code for the application."""
    global exit_code
    exit_code = code

@app.command()
def scan(
    ssp: str = typer.Argument(..., help="Path to FedRAMP OSCAL SSP file"),
    mapping: str = typer.Option("mappings/fedramp_il4.json", help="Path to control mapping file"),
    output: Optional[str] = typer.Option(None, help="Output directory for scan results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Scan a FedRAMP SSP for DoD IL4 compliance gaps"""
    
    # Validate inputs
    if not os.path.exists(ssp):
        console.print(f"[bold red]ERROR:[/] SSP file not found: {ssp}")
        set_exit_code(1)
        raise typer.Exit(1)
    
    if not os.path.exists(mapping):
        # Check if it's in the default mappings directory
        alt_mapping_path = str(Path(__file__).parent.parent / mapping)
        if os.path.exists(alt_mapping_path):
            mapping = alt_mapping_path
        else:
            console.print(f"[bold red]ERROR:[/] Mapping file not found: {mapping}")
            console.print("Make sure the mapping file exists or use --mapping to specify a custom path.")
            set_exit_code(1)
            raise typer.Exit(1)
    
    # Create output directory if specified and doesn't exist
    if output:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Display start banner
        console.print(Panel.fit(
            "[bold blue]FedRAMP Moderate → DoD IL4 Gap Scanner[/]",
            subtitle="Starting scan...",
        ))
        
        # Initialize audit logger with verbose mode if requested
        audit_logger = AuditLogger()
        
        # Create scanner
        scanner = IL4Scanner(audit_logger=audit_logger)
        
        # Run scan
        console.print(f"Scanning [cyan]{os.path.basename(ssp)}[/] using mapping [cyan]{os.path.basename(mapping)}[/]")
        with console.status("[bold green]Scanning...[/]"):
            result = scanner.scan(ssp, mapping, output)
        
        # Display results
        _display_scan_results(result)
        
        return 0
    
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] {str(e)}")
        if verbose:
            console.print_exception()
        set_exit_code(1)
        raise typer.Exit(1)

@app.command()
def wizard():
    """Interactive wizard to guide you through running a scan"""
    try:
        console.print(Panel.fit("[bold blue]FedRAMP Moderate → DoD IL4 Gap Scanner Wizard[/]"))
        
        # Ask for SSP file
        console.print("[bold]Step 1:[/] Select the OSCAL SSP file to scan")
        ssp_path = typer.prompt("Enter path to SSP file")
        
        # Validate SSP file
        if not os.path.exists(ssp_path):
            console.print(f"[bold red]ERROR:[/] File not found: {ssp_path}")
            set_exit_code(1)
            raise typer.Exit(1)
        
        # Ask for mapping file
        console.print("[bold]Step 2:[/] Select the control mapping file")
        default_mapping = "mappings/fedramp_il4.json"
        alt_mapping_path = str(Path(__file__).parent.parent / default_mapping)
        
        if os.path.exists(default_mapping):
            mapping_path = typer.prompt(f"Enter path to mapping file", default=default_mapping)
        elif os.path.exists(alt_mapping_path):
            mapping_path = typer.prompt(f"Enter path to mapping file", default=alt_mapping_path)
        else:
            mapping_path = typer.prompt("Enter path to mapping file")
        
        # Validate mapping file
        if not os.path.exists(mapping_path):
            console.print(f"[bold red]ERROR:[/] File not found: {mapping_path}")
            set_exit_code(1)
            raise typer.Exit(1)
        
        # Ask for output directory
        console.print("[bold]Step 3:[/] Select output directory for reports")
        default_output = os.path.join(os.getcwd(), "reports")
        output_dir = typer.prompt("Enter output directory path", default=default_output)
        
        # Run the scanner directly, don't call scan() function to avoid exit code issues
        # Initialize audit logger
        audit_logger = AuditLogger()
        
        # Create scanner
        scanner = IL4Scanner(audit_logger=audit_logger)
        
        # Run scan
        console.print(f"Scanning [cyan]{os.path.basename(ssp_path)}[/] using mapping [cyan]{os.path.basename(mapping_path)}[/]")
        with console.status("[bold green]Scanning...[/]"):
            result = scanner.scan(ssp_path, mapping_path, output_dir)
        
        # Make sure we have all required fields
        if "elapsed_time" not in result:
            result["elapsed_time"] = 0.0
            
        # Display results
        _display_scan_results(result)
        
        return 0
        
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] {str(e)}")
        set_exit_code(1)
        raise typer.Exit(1)

@app.command()
def verify_mapping(mapping: str = typer.Argument(..., help="Path to control mapping file")):
    """Verify the integrity of a control mapping file"""
    from fedramp_il4_scanner.analyzer import GapAnalyzer
    
    if not os.path.exists(mapping):
        console.print(f"[bold red]ERROR:[/] Mapping file not found: {mapping}")
        set_exit_code(1)
        raise typer.Exit(1)
    
    try:
        analyzer = GapAnalyzer(mapping)
        valid = analyzer.verify_mapping_integrity()
        
        if valid:
            console.print(f"[bold green]VALID:[/] Mapping file {mapping} passed integrity checks")
            return 0
        else:
            console.print(f"[bold red]INVALID:[/] Mapping file {mapping} failed integrity checks")
            set_exit_code(1)
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] {str(e)}")
        set_exit_code(1)
        raise typer.Exit(1)

def _display_scan_results(result: dict):
    """Display scan results in a nice format"""
    console.print("\n[bold green]✅ Scan Complete![/]")
    
    # Display summary
    console.print(Panel.fit(
        f"[bold]Scan ID:[/] {result['scan_id']}\n"
        f"[bold]Controls Analyzed:[/] {result['controls_analyzed']}\n"
        f"[bold]Gaps Identified:[/] {result['gaps_identified']}\n"
        f"[bold]Compliance Percentage:[/] {result['compliance_percentage']}%\n"
        f"[bold]Elapsed Time:[/] {result['elapsed_time']} seconds\n",
        title="Scan Summary"
    ))
    
    # Display report location
    console.print(f"\nDetailed reports available at: [cyan]{result['report_path']}[/]")

def main():
    """Main entry point for the CLI."""
    try:
        app()
    finally:
        # Use the global exit code
        sys.exit(exit_code)

if __name__ == "__main__":
    main()