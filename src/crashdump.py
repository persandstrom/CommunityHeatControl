
import sys
import time

def write(e: Exception):
    """ Write Exception to file """
    try:
        with open("error.log", "w") as f:
            f.write("\n" + "="*50 + "\n")
            f.write(f"Error at {time.ticks_ms()}ms\n")
            f.write(f"Exception: {type(e).__name__}: {str(e)}\n")
            f.write("-"*50 + "\n")
            sys.print_exception(e, f)  # This writes the full traceback
            f.write("="*50 + "\n")
        print("Error logged to error.log")
    except Exception as log_error:
        print(f"Failed to log error: {log_error}")

def read():
    """ Get last exception as string """
    try:
        with open("error.log", "r") as f:
            return f.read()
    except OSError:
        return "No error log found"

