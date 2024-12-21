"""Entry to Zeno. Parses TOML file, starts server, and runs the pipeline."""

import sys
from typing import Dict, Union
import pandas as pd

import pkg_resources
import uvicorn
from multiprocess import Process  # type: ignore

from zeno.api import ZenoParameters
from zeno.backend import ZenoBackend
from zeno.server import get_server
from zeno.setup import setup_zeno
from zeno.util import is_notebook, read_config

# Global variable to hold the Zeno server process.
# This is used to kill the server when re-running in a notebook.
ZENO_SERVER_PROCESS = None


def command_line():
    if len(sys.argv) == 1 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print(
            "\n \033[1mZeno\033[0m",
            pkg_resources.get_distribution("zenoml-next").version,
            " - Machine learning evaluation framework.",
            "\n\n",
            "\033[1mUSAGE \033[0m \n\t",
            "zeno [-h] [-v] <config.toml>",
            "\n\n",
            "\033[1mARGUMENTS \033[0m \n\t",
            "<config.toml>\t\tZeno configuration file.\n\n"
            "\033[1m GLOBAL OPTIONS \033[0m \n\t",
            "-h (--help)\t\tDisplay this help message.\n"
            "\t -v (--version)\t\tDisplay this application version.\n",
        )

        sys.exit(0)

    if len(sys.argv) != 2:
        print(
            "ERROR: Zeno take one argument, either a configuration TOML file"
            + " or the keyword 'init'. "
            + "{0} arguments were passed.",
            len(sys.argv),
        )
        sys.exit(1)

    if sys.argv[1] == "-v" or sys.argv[1] == "--version":
        print(pkg_resources.get_distribution("zenoml").version)
        sys.exit(0)

    if sys.argv[1] == "init" or sys.argv[1] == "i":
        setup_zeno()
    else:
        zeno(sys.argv[1])


def run_zeno(params: ZenoParameters):
    zeno = ZenoBackend(params)
    app = get_server(zeno)

    zeno.start_processing()

    print(
        "\n\033[1mZeno\033[0m running on http://{}:{}\n".format(
            params.host, params.port
        )
    )
    uvicorn.run(app, host=params.host, port=params.port, log_level="error")


def zeno(args: Union[str, ZenoParameters, Dict]):
    """Main entrypoint for Zeno. This is called directly by the user in a notebook or
    script, or called by the command_line function when run by CLI.

    Args:
        args (Union[str, ZenoParameters, Dict]): The configuration for Zeno.
        ZenoParameters or dict when called from Python, str if called from commandline.
    """

    params = read_config(args)

    if params.serve:
        global ZENO_SERVER_PROCESS
        if ZENO_SERVER_PROCESS is not None:
            ZENO_SERVER_PROCESS.terminate()

        ZENO_SERVER_PROCESS = Process(
            target=run_zeno,
            args=(params,),
        )
        ZENO_SERVER_PROCESS.start()

        if not is_notebook():
            ZENO_SERVER_PROCESS.join()
    else:
        zeno = ZenoBackend(params)
        return zeno


def zeno_next(df: pd.DataFrame, data_path: str, data_column: str, port: int):
    """Main entrypoint for Zeno. This is called directly by the user in a notebook or
    script, or called by the command_line function when run by CLI.

    Args:
        df (pd.DataFrame): The dataframe to be served. contains at least one column with image paths.
        data_path (str): The root path to the data. (e.g. /path/to/data)
        data_column (str): The column name in the dataframe that contains the image paths.
        port (int): The port to run the server on.
    """

    args = {
        "metadata": df,
        "view": "image-classification",
        "data_path": data_path,
        "data_column": data_column,
        "id_column": data_column,
        "label_column": data_column,
        "batch_size": 1000,
        "port": port,
    }

    params = read_config(args)

    if params.serve:
        global ZENO_SERVER_PROCESS
        if ZENO_SERVER_PROCESS is not None:
            ZENO_SERVER_PROCESS.terminate()

        ZENO_SERVER_PROCESS = Process(
            target=run_zeno,
            args=(params,),
        )
        ZENO_SERVER_PROCESS.start()

        if not is_notebook():
            ZENO_SERVER_PROCESS.join()
    else:
        zeno = ZenoBackend(params)
        return zeno
