import shutil

if shutil.which("Xvfb") is None:
    raise EnvironmentError("Xvfb is missing. Please install it first.")
