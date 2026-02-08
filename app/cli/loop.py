from app.cli.context import CLIContext
from app.cli.commands import handle_command
from app.services.user_service import ServiceError
from app.storage import DataStore
try:
    import readline
except ImportError:
    import pyreadline3 as readline

def run_cli() -> None:
    store = DataStore()
    state = store.load()

    ctx = CLIContext()

    print("Demo_planner_v2 CLI")
    print("Type 'help' to see commands.")

    while True:
        try:
            raw = input(ctx.format_prompt(state)).strip()
            if not raw:
                continue

            if raw in {"exit", "quit"}:
                store.save(state)
                print("State saved. Bye.")
                break

            handle_command(state, ctx, raw)

        except ServiceError as e:
            print(f"Error: {e}")

        except KeyboardInterrupt:
            store.save(state)
            print("State saved. Bye.")
            break
