import os
import SimpleHTTPServer
import urlparse
import subprocess

class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

  def do_GET(self):

    parsedParameters = urlparse.urlparse(self.path)
    queryParsed = urlparse.parse_qs(parsedParameters.query)
    
    path = parsedParameters.path
    print "Path is ", path
    
    if path == '/tempraw.html':
      self.TemperatureRequest('~/templog/%s' %
                         queryParsed.get('date',['2013/11/09'])[0])
    elif  path == '/temp.html':
      self.TemperatureGraphRequest(
                         queryParsed.get('date',['2013/11/09'])[0])
    elif  path == '/temp.js':
      self.TemperatureRequestAsJS('~/templog/%s' %
                         queryParsed.get('date',['2013/11/09'])[0])
    elif path == '/photo.html':

      width = queryParsed.get('width',['300'])[0]
      height = queryParsed.get('height',['300'])[0]
      timeout = queryParsed.get('timeout',['500'])[0]
      filename = queryParsed.get('filename',['image.jpg'])[0]

      subprocess.call(["raspistill","-n",
         "--width",width,
         "--height",height,
         "--timeout",timeout,
         "-o",filename])

      self.processMyRequest(filename)

    else:

      SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self);

  def BasicHeaders(self):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()

    self.wfile.write("<!DOCTYPE html>\n")
    self.wfile.write("<html>\n")
    self.wfile.write("<body>\n")

  def Footer(self):
    self.wfile.write("</body>\n")
    self.wfile.write("</html>\n")
    
  def processMyRequest(self, filename):
    self.BasicHeaders()
    self.wfile.write("<h1>Image: " + filename + "</h1>\n")
    self.wfile.write('<img src="./'+filename+'" alt="camera">\n')
    self.Footer()
    self.wfile.close()

  def TemperatureRequest(self, filename):
    self.BasicHeaders()
    with open(os.path.expanduser(filename)) as myfile:
      content = myfile.readlines()
    self.wfile.write('<br>\n'.join(content))
    self.Footer()
    self.wfile.close()
    
  def TemperatureGraphRequest(self, datestring):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()

    self.wfile.write("<!DOCTYPE html>\n")
    self.wfile.write("<html>\n")
    self.wfile.write("<script src='/dygraph-combined.js' ></script>\n")
    self.wfile.write("<script src='/temp.js?date=%s' ></script>\n" % datestring)
    self.wfile.write("""<body>
                     <div id="graphdiv2" />
<script>
new Dygraph(document.getElementById("graphdiv2"),
              temperatures,
              {
                labels: [ "t", "C", "A", "B" ]
              });

</script>
</body>
</html>
"""
)
    self.wfile.close()
    
  def TemperatureRequestAsJS(self, filename):
    """Send it as a javascript array for dygraphs to plot"""
    self.send_response(200)
    self.send_header('Content-Type', 'text/javascript')
    self.end_headers()
    self.wfile.write('temperatures = [')
    with open(os.path.expanduser(filename)) as myfile:
      content = myfile.readlines()
    for l in content:
      a= l.strip().split(' ')
      thetime=a[1]
      tf = thetime.split(':')
      timesecs = int(tf[0]) * 3600 + int(tf[1]) * 60 + int(tf[2])
      temps=[]
      for fields in a[2:]:
        parts = fields.split(':')
        temps.append(parts[1])
      self.wfile.write('[%d, %s],\n' % (timesecs, ','.join(temps)))
    self.wfile.write('];')
    self.wfile.close()
