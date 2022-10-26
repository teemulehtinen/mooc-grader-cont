import logging
from datetime import datetime
from flask import Flask, request

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def debug_dict(d, form=lambda v: str(v)):
  return '\n'.join(f'  {k}={v}' for k, v in d.items(multi=True))

app = Flask(__name__)

@app.route('/', methods=None, defaults={'path': ''})
@app.route('/<path:path>', methods=None)
def any_request(path):
  print(f'{datetime.now()} {request.scheme} {request.method} /{path}')
  if request.args:
    print(f'URL args:\n{debug_dict(request.args)}')
  if request.form:
    print(f'Form:\n{debug_dict(request.form)}')
  if request.files:
    print(f'Files:\n{debug_dict(request.files, form=lambda f: f.filename)}')
  return 'Ok'
