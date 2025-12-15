#!/usr/bin/env python3
"""
Simple CLI for maintenance tasks: import-data and reset-db.
Usage:
  python manage.py import-data path/to/file.json
  python manage.py reset-db
"""
import click
from init import create_app

app = create_app()

# import functions from app module (they expect to run inside app_context)
from app import input_data_from_json, delete_all, reset_content

@click.group()
def cli():
    pass


@cli.command("import-data")
@click.argument("path", type=click.Path(exists=True))
def import_data(path):
    """Import JSON data (leagues/seasons/divisions/results) from PATH."""
    with app.app_context():
        click.echo(f"Importing data from {path} ...")
        with open(path, "r") as f:
            input_data_from_json(f)
        click.echo("Import finished.")


@cli.command("reset-db")
@click.confirmation_option(prompt="This will delete all data. Are you sure?")
def reset_db():
    """Delete all domain data (leagues, seasons, players, results, rankings)."""
    with app.app_context():
        click.echo("Clearing database content...")
        delete_all()
        click.echo("Done.")


@cli.command("reload-data")
def reload_data():
    with app.app_context():
        reset_content()
        click.echo("Done.")


if __name__ == "__main__":
    cli()