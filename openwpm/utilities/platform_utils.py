import json
import os
import subprocess
from collections import OrderedDict
from copy import deepcopy
from sys import platform

from tabulate import tabulate

from openwpm.config import ConfigEncoder


def parse_http_stack_trace_str(trace_str):
    """Parse a stacktrace string and return an array of dict."""
    stack_trace = []
    frames = trace_str.split("\n")
    for frame in frames:
        try:
            func_name, rest = frame.split("@", 1)
            rest, async_cause = rest.rsplit(";", 1)
            filename, line_no, col_no = rest.rsplit(":", 2)
            stack_trace.append(
                {
                    "func_name": func_name,
                    "filename": filename,
                    "line_no": line_no,
                    "col_no": col_no,
                    "async_cause": async_cause,
                }
            )
        except Exception as exc:
            print("Exception parsing the stack frame %s %s" % (frame, exc))
    return stack_trace


def get_firefox_binary_path():
    """
    If ../../firefox-bin/firefox-bin or os.environ["FIREFOX_BINARY"] exists,
    return it. Else, throw a RuntimeError.
    """
    if "FIREFOX_BINARY" in os.environ:
        firefox_binary_path = os.environ["FIREFOX_BINARY"]
        if not os.path.isfile(firefox_binary_path):
            raise RuntimeError(
                "No file found at the path specified in "
                "environment variable `FIREFOX_BINARY`."
                "Current `FIREFOX_BINARY`: %s" % firefox_binary_path
            )
        return firefox_binary_path

    root_dir = os.path.dirname(__file__) + "/../.."
    if platform == "darwin":
        firefox_binary_path = os.path.abspath(
            root_dir + "/Nightly.app/Contents/MacOS/firefox-bin"
        )
    else:
        firefox_binary_path = os.path.abspath(root_dir + "/firefox-bin/firefox-bin")

    if not os.path.isfile(firefox_binary_path):
        raise RuntimeError(
            "The `firefox-bin/firefox-bin` binary is not found in the root "
            "of the  OpenWPM directory (did you run the install script "
            "(`install.sh`)?). Alternatively, you can specify a binary "
            "location using the OS environment variable FIREFOX_BINARY."
        )
    return firefox_binary_path

## TFS: Add Tor Binary path
def get_torbrowser_binary_path():
    """
    If ../../firefox-bin/firefox-bin or os.environ["TORBROWSER_BINARY"] exists,
    return it. Else, throw a RuntimeError.
    """
    if "TORBROWSER_BINARY" in os.environ:
        torbrowser_binary_path = os.environ["TORBROWSER_BINARY"]
        if not os.path.isfile(torbrowser_binary_path):
            raise RuntimeError(
                "No file found at the path specified in "
                "environment variable `TORBROWSER_BINARY`."
                "Current `TORBROWSER_BINARY`: %s" % torbrowser_binary_path
            )
        return torbrowser_binary_path

    root_dir = os.path.dirname(__file__) + "/../.."
    if platform == "darwin":
        torbrowser_binary_path = os.path.abspath(
            root_dir + "/Nightly.app/Contents/MacOS/Tor/firefox-bin"
        )
    else:
        torbrowser_binary_path = os.path.abspath(root_dir
            + "/Tor/tor-browser/Browser/firefox")

    if not os.path.isfile(torbrowser_binary_path):
        raise RuntimeError(
            "The `Tor/tor-browser/Browser/firefox` binary is not found "
            "in the root of the  OpenWPM directory (did you run the "
            "install script (`install.sh`)?). Alternatively, you can "
            "specify a binary location using the OS environment variable"
            " TORBROWSER_BINARY."
        )
    return torbrowser_binary_path

## TFS: Add Tor Binary path.
def get_torbrowser_profile_path(slider_setting):
    """
    If Tor/tor-browser/Browser/TorBrowser/Data/Browser or
    os.environ["TORBROWSER_PROFILE"] exists, return it. Else, throw a
    RuntimeError.
    """
    if "TORBROWSER_PROFILE" in os.environ:
        torbrowser_binary_path = os.environ["TORBROWSER_PROFILE"]
        total_path = f'{torbrowser_binary_path}/{slider_setting}'
        if not os.path.isdir(total_path):
            raise RuntimeError(
                "No file found at the path specified in "
                "environment variable `TORBROWSER_PROFILE`."
                f"Current `TORBROWSER_PROFILE`: {torbrowser_binary_path}.\n"
                f"Current slider setting: {slider_setting}."
            )
        return torbrowser_profile_path + f'/{slider_setting}'

    root_dir = os.path.dirname(__file__) + "/../.."
    # TFS: TODO: Modify the code below.
    if platform == "darwin":
        torbrowser_binary_path = os.path.abspath(
            root_dir + "/Nightly.app/Contents/MacOS/Tor/firefox-bin"
        )
    else:
        torbrowser_profile_path = os.path.abspath(root_dir
            + f"/Tor/tor-browser/Browser/TorBrowser/Data/Browser/{slider_setting}")

    if not os.path.isdir(torbrowser_profile_path):
        raise RuntimeError(
            f"The `Tor/tor-browser/Browser/TorBrowser/Data/Browser/{slider_level}`"
            " directory is not found in the root of the  OpenWPM directory. "
            "You can specify a profile location using the OS environment "
            "variable TORBROWSER_PROFILE."
        )
    return torbrowser_profile_path

def get_version():
    """Return OpenWPM version tag/current commit and Firefox version"""
    try:
        openwpm = subprocess.check_output(
            ["git", "describe", "--tags", "--always"]
        ).strip()
    except subprocess.CalledProcessError:
        ver = os.path.join(os.path.dirname(__file__), "../../VERSION")
        with open(ver, "r") as f:
            openwpm = f.readline().strip()

    firefox_binary_path = get_firefox_binary_path()
    try:
        firefox = subprocess.check_output([firefox_binary_path, "--version"])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Firefox not found. " " Did you run `./install.sh`?") from e

    ff = firefox.split()[-1]
    # TFS: return Tor Browser version as well.
    #return openwpm, ff
    torbrowser_dir_path = os.path.dirname(get_torbrowser_binary_path())
    torbrowser_version_path = os.path.join(torbrowser_dir_path, 'tbb_version.json')
    try:
        with open(torbrowser_version_path, 'r') as json_file:
            tor = "Tor Browser Version" + json.loads(json_file.read())['version']
    except FileNotFoundError:
        raise RuntimeError("Tor Browser version info not found.") from e
    except PermissionError:
        raise RuntimeError("Tor Browser version info cannot be read.") from e
    except json.JSONDecodeError:
        raise RuntimeError("Tor Browser version info not formatted properly.") from e
    return openwpm, ff, tor


def get_configuration_string(manager_params, browser_params, versions):
    """Construct a well-formatted string for {manager,browser}params

    Constructs a pretty printed string of all parameters. The config
    dictionaries are split to try to avoid line wrapping for reasonably
    size terminal windows.
    """

    config_str = "\n\nOpenWPM Version: %s\nFirefox Version: %s\n" % versions
    config_str += "\n========== Manager Configuration ==========\n"

    config_str += json.dumps(
        manager_params.to_dict(),
        sort_keys=True,
        indent=2,
        separators=(",", ": "),
        cls=ConfigEncoder,
    )
    config_str += "\n\n========== Browser Configuration ==========\n"

    print_params = [deepcopy(x.to_dict()) for x in browser_params]
    table_input = list()
    profile_dirs = OrderedDict()
    archive_dirs = OrderedDict()
    js_config = OrderedDict()
    profile_all_none = archive_all_none = True
    for item in print_params:
        browser_id = item["browser_id"]

        # Update print flags
        if item["seed_tar"] is not None:
            profile_all_none = False
        if item["profile_archive_dir"] is not None:
            archive_all_none = False

        # Separate out long profile directory strings
        profile_dirs[browser_id] = str(item.pop("seed_tar"))
        archive_dirs[browser_id] = str(item.pop("profile_archive_dir"))
        js_config[browser_id] = item.pop("cleaned_js_instrument_settings")

        # Copy items in sorted order
        dct = OrderedDict()
        dct["browser_id"] = browser_id
        for key in sorted(item.keys()):
            dct[key] = item[key]
        table_input.append(dct)

    key_dict = OrderedDict()
    counter = 0
    for key in table_input[0].keys():
        key_dict[key] = counter
        counter += 1
    config_str += "Keys:\n"
    config_str += json.dumps(key_dict, indent=2, separators=(",", ": "))
    config_str += "\n\n"
    config_str += tabulate(table_input, headers=key_dict)

    config_str += "\n\n========== JS Instrument Settings ==========\n"
    config_str += json.dumps(js_config, indent=None, separators=(",", ":"))

    config_str += "\n\n========== Input profile tar files ==========\n"
    if profile_all_none:
        config_str += "  No profile tar files specified"
    else:
        config_str += json.dumps(profile_dirs, indent=2, separators=(",", ": "))

    config_str += "\n\n========== Output (archive) profile dirs ==========\n"
    if archive_all_none:
        config_str += "  No profile archive directories specified"
    else:
        config_str += json.dumps(archive_dirs, indent=2, separators=(",", ": "))

    config_str += "\n\n"
    return config_str
