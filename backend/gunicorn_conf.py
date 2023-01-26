import multiprocessing

name = "gunicorn config for FastAPI"
accesslog = "/home/ivan/betting/gunicorn_access.log"
errorlog = "/home/ivan/betting/gunicorn_error.log"

bind = 'unix:/home/ivan/betting/gunicorn.sock'

worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1024
backlog = 2048
max_requests = 5120

debug = False
reload = debug
preload_app = True
daemon = False
