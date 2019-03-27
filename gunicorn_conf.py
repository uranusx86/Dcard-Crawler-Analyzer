import json

workers_per_core_str = "1"
web_concurrency_str = None
host = "0.0.0.0"
port = "80"
bind_env = None
use_loglevel = "info"
if bind_env:
    use_bind = bind_env
else:
    use_bind = f"{host}:{port}"

cores = 1
workers_per_core = float(workers_per_core_str)
default_web_concurrency = workers_per_core * cores
if web_concurrency_str:
    web_concurrency = int(web_concurrency_str)
    assert web_concurrency > 0
else:
    web_concurrency = int(default_web_concurrency)

# Gunicorn config variables
loglevel = use_loglevel
workers = web_concurrency
bind = use_bind
keepalive = 120
errorlog = "-"

# For debugging and testing
log_data = {
    "loglevel": loglevel,
    "workers": workers,
    "bind": bind,
    # Additional, non-gunicorn variables
    "workers_per_core": workers_per_core,
    "host": host,
    "port": port,
}
print(json.dumps(log_data))