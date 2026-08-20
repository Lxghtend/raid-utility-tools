import os
import sys
import subprocess

repo_path = os.path.dirname(os.path.abspath(__file__))
 
def check_for_update():
    """
    Compares local HEAD against the remote's latest commit on the current branch.
    Returns (is_behind: bool, local_hash: str, remote_hash: str).
    Returns (False, "", "") if the check fails for any reason (offline, git
    missing, not a repo, etc.) so callers can just skip updating silently.
    """
    print("Checking for update...")
    try:
        # make sure we know what the remote actually has, without touching local files
        subprocess.run(
            ["git", "fetch"],
            cwd=repo_path, check=True, capture_output=True, text=True, timeout=10
        )
 
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, check=True, capture_output=True, text=True
        ).stdout.strip()
 
        remote = subprocess.run(
            ["git", "rev-parse", "@{u}"],
            cwd=repo_path, check=True, capture_output=True, text=True
        ).stdout.strip()
 
        return ((local != remote), local[:7], remote[:7])
 
    except Exception as e:
        print(f"Update check skipped: {e}")
        return (False, "", "")

def trigger_update(tool_dir, main_script="main.py"):
    """
    Spawns update.bat (same folder as this file) in a detached process,
    passing this process's PID plus where to relaunch from, then exits
    this app so the batch script can safely prompt and git pull without
    file locks in the way.

    tool_dir: absolute path to the calling tool's folder (e.g. .../az-tool)
    main_script: filename of that tool's entry point, relative to tool_dir
    """
    repo_root = os.path.dirname(os.path.abspath(__file__))
    updater_bat = os.path.join(repo_root, "update.bat")
    main_script_path = os.path.join(tool_dir, main_script)

    if not os.path.exists(updater_bat):
        print(f"update.bat not found at repo root ({updater_bat}), exiting...")
        return

    subprocess.Popen(
        [updater_bat, str(os.getpid()), tool_dir, main_script_path],
        creationflags=subprocess.CREATE_NEW_CONSOLE  # change to CREATE_NO_WINDOW to hide
    )

    sys.exit(0)
