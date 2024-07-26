from ..query_executor import execute_query
from ..db_operations.factory import DatabaseFactory
import click
from ..utils.print import print_success, print_info, create_box, print_error
from ..sql_validator import sanitize_sql_query
from tabulate import tabulate


def db_query_worker(sql_queue, state):
    context = state['context']
    try:
        while True:
            sql = sql_queue.get()
            if sql is None:  # Exit signal
                break
            try:
                db = DatabaseFactory.get_database()
                result, column_names = db.execute_query_with_column_names(sql)
                state['sql_query'] = sql
                state['db_result'] = (result, column_names)
                print_success("\nQuery executed successfully!")
            except Exception as e:
                print_error(f"\nError executing query: {str(e)}")
                state['db_result'] = (str(e), None)
            finally:
                state['execution_complete'].set()
    except Exception as e:
        print_error(f"Unexpected error in db_query_worker: {str(e)}")
    finally:
        state['execution_complete'].set()


def print_formatted_result(result, column_names):
    if not result:
        print_info("No results found.")
        return
    if len(result) == 1 and len(result[0]) == 1:
        # Single value result
        value = result[0][0]
        box = create_box("Query Result", f"{column_names[0]}: {value}", "")
        click.echo(box)
    else:
        # Multiple rows or columns
        table = tabulate(result, headers=column_names, tablefmt="grid")
        click.echo(table)
