import logging
from flask import Flask, request

def strip_empty_lines(v):
  return '\n'.join(r for r in str(v).split('\n') if r.strip() != '').strip()

def debug_dict(d, form=lambda v: strip_empty_lines(v)):
  return '\n'.join(f'  {k}={form(v)}' for k, v in d.items(multi=True))

def debug_request(r):
  lines = []
  if r.args:
    lines.extend(['URL:', debug_dict(r.args)])
  if r.form:
    lines.extend(['POST:', debug_dict(r.form)])
  if r.files:
    lines.extend(['Files:', debug_dict(r.files, form=lambda f: f.filename)])
  return '\n'.join(lines)

log = logging.getLogger('content')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
log.addHandler(handler)

app = Flask(__name__)

ALL = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'CONNECT', 'TRACE']
@app.route('/', methods=ALL, defaults={'path': ''})
@app.route('/<path:path>', methods=ALL)
def any_request(path):
  log.info(debug_request(request))
  return 'Ok'
