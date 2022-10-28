FROM python:3.8-alpine
RUN pip install flask
COPY DebugHTTPServer.py /src/
EXPOSE 5000
CMD [ \
  "python3", "-m", "flask", \
  "-A", "/src/DebugHTTPServer.py", \
  "run", \
  "-h", "0.0.0.0", \
  "-p", "5000" \
]
