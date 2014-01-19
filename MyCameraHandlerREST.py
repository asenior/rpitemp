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
    self.wfile.write('<br><a href="temp.html">Temperatures</a>\n')
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
    """Returns an HTML page with two dygraphs and links.

    First is daily max/min temperatures for all time recorded.
    Second is minute temps for the given day (a string YYYY/MM/DD)
    Temperatures are provided as javascript via separate requests,
    in the requested units (a string 'C' or 'F'
    """
    self.send_response(200)
    self.send_header('Content-Type', 'text/html')
    self.end_headers()
    dt = datetime.datetime.strptime(datestring, "%Y/%m/%d")
    delta = datetime.timedelta(1)  # 1 Day
    prevday=  (dt - delta).strftime("%Y/%m/%d")
    nextday= (dt + delta).strftime("%Y/%m/%d")
    self.wfile.write("<!DOCTYPE html>\n")
    self.wfile.write("<html>\n")
    self.wfile.write("<script src='/dygraph-combined.js' ></script>\n")
    self.wfile.write("<script src='/dailytemp.js?units=%s' ></script>\n" %
                       units)
    self.wfile.write("<script src='/temp.js?date=%s&units=%s' ></script>\n" %
                       (datestring, units))
    self.wfile.write("""
<body>
  <h2>%s</h2>
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
<a href="temp.html?date=%s">%s&lt;&lt;</a> &nbsp;&nbsp;&nbsp;&nbsp;
<a href="temp.html?date=%s">&gt;&gt;%s</a> <br>
<a href="photo.html?width=800&height=600">Photo</a>
</body>
</html>
""" % (dt.strftime("%A %d %B %Y"), units[0], units[0], prevday, prevday, nextday, nextday)
)
    self.wfile.close()

  @staticmethod
  def CanonicalUnits(units):
    if units and (units[0] == 'c' or units[0] == 'C'):
        return 'C'
    else:
        return 'F'

  @staticmethod
  def ConvertTempStringFromC(temp, units):
    """Takes a string of floating point Celsius temp
    and returns it as a floating point string in the
    requested units."""
    if MyHandler.CanonicalUnits(units) == 'C':
      return temp
    else:
      return "%.2f" % (1.8 * float(temp) + 32.0)

  @staticmethod
  def ConvertTempStringListFromC(temp, units):
    """Takes a list of strings of floating point Celsius temps
    and returns them as a list of floating points strings in the
    requested units."""
    return [MyHandler.ConvertTempStringFromC(t,units) for t in temp]

  def TemperatureRequestAsJS(self, filename, units):
    """Send the file's data as a javascript array for dygraphs to plot"""
    self.send_response(200)
    self.send_header('Content-Type', 'text/javascript')
    self.end_headers()
    self.wfile.write('temperatures = [')
    with open(os.path.expanduser(filename)) as myfile:
      content = myfile.readlines()
#    labels = []
    labels = []
    # First build a list of all the labels.
    for l in content:
      a = l.strip().split(' ')
      for fields in a[2:]:
        parts = fields.split(':')
        if not parts[0] in labels:
          labels.append('%s' % parts[0])
    labels= sorted(labels)
 
    # Now build the lines with the labels in a consistent order.
    for l in content:
      a = l.strip().split(' ')
      thedate = a[0]
      thetime = a[1]
      tf = thetime.split(':')
      timesecs = int(tf[0]) + (int(tf[1]) * 60 + int(tf[2]))/3600.0
      temps = ['NaN' for i in labels]
      for fields in a[2:]:
        parts = fields.split(':')
        assert parts[0] in labels
        temperature = parts[1]
        if float(temperature) != 85.0:  # 85C seems to be malfunction.
          temps[labels.index(parts[0])] = self.ConvertTempStringFromC(temperature, units)
#        temps.append(parts[1])
      self.wfile.write(
        '[new Date(\"%s %s\"), %s],\n' %
           (thedate, thetime, ','.join(temps)))
    self.wfile.write('];\ntemplabels = [%s];\n' % ','.join(['"%s"' % x.lstrip('0') for x in ['Date'] + labels]))
    self.wfile.close()

  def DailyTemperatureRequestAsJS(self, filename, units):
    """Send the file's data as a javascript array for dygraphs to plot.

    The file is YYYY/MM/DD <device>:mean:min:max <device>...
    """
    self.send_response(200)
    self.send_header('Content-Type', 'text/javascript')
    self.end_headers()
    units = self.CanonicalUnits(units)
    self.wfile.write('dailytemperatures = [\n')
    with open(os.path.expanduser(filename)) as myfile:
      content = myfile.readlines()
    labels = []
    # First build a list of all the labels.
    for l in content:
      a= l.strip().split(' ')
      thedate=a[0]
      temps = []
      for fields in a[1:]:
        parts = fields.split(':')
        if not parts[0] in labels:
          labels.append(parts[0])
    # TODO sort the labels.
    labels= sorted(labels)
    # Now build a javascript array with all the data.
    for l in content:
      a= l.strip().split(' ')
      temps = ['NaN' for i in labels]
      thedate = a[0]
      these_temps = {}
      # Put all the temperatures into a dict.
      for fields in a[1:]:
        parts = fields.split(':')
        assert parts[0] in labels
        temps[labels.index(parts[0])] = "[%s]" % ",".join(
          self.ConvertTempStringListFromC(parts[1:], units))

      # Now pull the temperatures out in the order of the labels.       
        # TODO Handle different devices / different order.
      self.wfile.write('[ new Date(\"%s\"), %s],\n' %
                       (thedate, ','.join(temps)))
      first = False
    self.wfile.write('];\n dailytemplabels = [%s];\n' % ','.join(
      ['"%s"' % x.lstrip('0') for x in ['Date'] + labels]))
    self.wfile.close()
