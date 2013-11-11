import os
import SimpleHTTPServer
import urlparse
import subprocess
import datetime

class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

  def do_GET(self):

    parsedParameters = urlparse.urlparse(self.path)
    queryParsed = urlparse.parse_qs(parsedParameters.query)
    
    path = parsedParameters.path
    print "Path is ", path
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    default_units = 'F'
    if path == '/tempraw.html':
      self.TemperatureRequest('~/templog/%s' %
                         queryParsed.get('date',[today])[0])
    elif  path == '/temp.html':
      self.TemperatureGraphRequest(
                         queryParsed.get('date',[today])[0],
	queryParsed.get('units',[default_units])[0])
    elif  path == '/temp.js':
      self.TemperatureRequestAsJS('~/templog/%s' %
                         queryParsed.get('date',[today])[0],
	queryParsed.get('units',[default_units])[0])
    elif  path == '/dailytemp.js':
      self.DailyTemperatureRequestAsJS('~/templog/maxmin',
	queryParsed.get('units',[default_units])[0])
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
    
  def TemperatureGraphRequest(self, datestring, units):
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()

    self.wfile.write("<!DOCTYPE html>\n")
    self.wfile.write("<html>\n")
    self.wfile.write("<script src='/dygraph-combined.js' ></script>\n")
    self.wfile.write("<script src='/dailytemp.js?units=%s' ></script>\n" %
                       units)
    self.wfile.write("<script src='/temp.js?date=%s&units=%s' ></script>\n" %
                       (datestring, units))
    self.wfile.write("""<body>
                     <div id="graphdivdaily"></div>
                     <div id="graphdiv2"></div>
<script>
new Dygraph(document.getElementById("graphdivdaily"),
              dailytemperatures,
              {
                customBars: true,
                labels: dailytemplabels,
                ylabel: 'Temperature (%s)',
              });
new Dygraph(document.getElementById("graphdiv2"),
              temperatures,
              {
                labels: templabels,
                ylabel: 'Temperature (%s)',
              });

</script>
</body>
</html>
""" % (units[0], units[0])
)
    self.wfile.close()

  def TemperatureRequestAsJS(self, filename, units):
    """Send the file's data as a javascript array for dygraphs to plot"""
    self.send_response(200)
    self.send_header('Content-Type', 'text/javascript')
    self.end_headers()
    offs = 32
    mult = 1.8
    if units and (units[0] == 'c' or units[0] == 'C'):
	mult = 1.0
	offs = 0.0
    self.wfile.write('temperatures = [')
    with open(os.path.expanduser(filename)) as myfile:
      content = myfile.readlines()
    labels = ['"Time"']
    first = True
    for l in content:
      a= l.strip().split(' ')
      thetime=a[1]
      tf = thetime.split(':')
      timesecs = int(tf[0]) + (int(tf[1]) * 60 + int(tf[2]))/3600.0
      temps = []
      for fields in a[2:]:
        parts = fields.split(':')
        temps.append("%.2f" % (offs + mult * float(parts[1])))
        if first:
          labels.append('"%s"' %parts[0])
      self.wfile.write('[%.2f, %s],\n' % (timesecs, ','.join(temps)))
      first = False
    self.wfile.write('];\n templabels = [%s];' % ','.join(labels))
    self.wfile.close()

  def DailyTemperatureRequestAsJS(self, filename, units):
    """Send the file's data as a javascript array for dygraphs to plot.

    The file is YYYY/MM/DD <device>:mean:min:max <device>...
    """
    self.send_response(200)
    self.send_header('Content-Type', 'text/javascript')
    self.end_headers()
    offs = 32
    mult = 1.8
    if units and (units[0] == 'c' or units[0] == 'C'):
	mult = 1.0
	offs = 0.0
    self.wfile.write('dailytemperatures = [\n')
    with open(os.path.expanduser(filename)) as myfile:
      content = myfile.readlines()
    labels = ['"Date"']
    first = True
    for l in content:
      a= l.strip().split(' ')
      thedate=a[0]
      temps = []
      for fields in a[1:]:
        parts = fields.split(':')
        temps.append("[%s]" % ",".join(parts[1:]))
        # TODO Handle different devices / different order.
        if first:
          labels.append('"%s"' % parts[0])
      self.wfile.write('[ new Date(\"%s\"), %s],\n' %
                       (thedate, ','.join(temps)))
      first = False
    self.wfile.write('];\n dailytemplabels = [%s];\n' % ','.join(labels))
    self.wfile.close()
