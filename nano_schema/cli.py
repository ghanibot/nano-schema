from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.syntax import Syntax
from rich import box
from rich.table import Table

app = typer.Typer(name="nano-schema", add_completion=False)
console = Console(force_terminal=True)


@app.command()
def extract(
    schema_file: Path = typer.Argument(..., help="Python file defining schema dataclass"),
    schema_class: str = typer.Argument(..., help="Dataclass name in file"),
    text: Optional[str] = typer.Argument(None, help="Text to extract from (or pipe stdin)"),
    provider: str = typer.Option("anthropic", "--provider", "-p"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    retries: int = typer.Option(3, "--retries", "-r"),
    json_output: bool = typer.Option(False, "--json", "-j"),
):
    """Extract structured data from text using a schema dataclass."""
    if text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            console.print("[red]Provide text as argument or via stdin[/red]")
            raise typer.Exit(1)

    # Load schema class from file
    import importlib.util
    spec = importlib.util.spec_from_file_location("_schema_module", str(schema_file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, schema_class, None)
    if cls is None:
        console.print(f"[red]Class '{schema_class}' not found in {schema_file}[/red]")
        raise typer.Exit(1)

    from nano_schema.extractor import SchemaExtractor
    extractor = SchemaExtractor(provider=provider, model=model, max_retries=retries)
    result = extractor.extract(cls, text)

    if json_output:
        import dataclasses
        out = dataclasses.asdict(result.data) if result.success and result.data else {"error": result.error}
        console.print(json.dumps(out, indent=2, ensure_ascii=False))
        raise typer.Exit(0 if result.success else 1)

    if result.success:
        console.print(f"\n[bold green]✓ Extracted[/bold green] [dim]{result.schema_name}[/dim] "
                      f"({result.attempts} attempt{'s' if result.attempts > 1 else ''}, "
                      f"{result.input_tokens + result.output_tokens} tokens)\n")
        import dataclasses
        data_dict = dataclasses.asdict(result.data)
        syntax = Syntax(json.dumps(data_dict, indent=2, ensure_ascii=False), "json", theme="monokai")
        console.print(syntax)
    else:
        console.print(f"\n[bold red]✗ Failed[/bold red] after {result.attempts} attempts")
        console.print(f"[red]{result.error}[/red]")
        if result.raw:
            console.print(f"\n[dim]Raw LLM response:[/dim]\n{result.raw[:500]}")
        raise typer.Exit(1)


@app.command()
def schema(
    schema_file: Path = typer.Argument(..., help="Python file defining schema dataclass"),
    schema_class: str = typer.Argument(..., help="Dataclass name in file"),
):
    """Print JSON Schema for a dataclass."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("_schema_module", str(schema_file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cls = getattr(module, schema_class)

    from nano_schema.schema_builder import build_json_schema
    s = build_json_schema(cls)
    syntax = Syntax(json.dumps(s, indent=2), "json", theme="monokai")
    console.print(syntax)


@app.command()
def providers():
    """List supported LLM providers."""
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("Provider")
    t.add_column("Env Var")
    t.add_column("Default Model")
    rows = [
        ("anthropic", "ANTHROPIC_API_KEY", "claude-haiku-4-5-20251001"),
        ("openai", "OPENAI_API_KEY", "gpt-4o-mini"),
        ("groq", "GROQ_API_KEY", "llama3-8b-8192"),
        ("mistral", "MISTRAL_API_KEY", "mistral-small-latest"),
        ("ollama", "(local)", "llama3.2"),
    ]
    for r in rows:
        t.add_row(*r)
    console.print("\n[bold]Supported providers[/bold]")
    console.print(t)
    console.print("[dim]Override model: NANO_SCHEMA_MODEL env var or --model flag[/dim]\n")
