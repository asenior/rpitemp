"""Basic web server with optional port."""
import sys
import SocketServer
import MyCameraHandlerREST

PORT = 8000

if len(sys.argv) > 1:
  PORT = int(sys.argv[1])
  print 'Port set to %d' % PORT
Handler = MyCameraHandlerREST.MyHandler

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
try:
  httpd.serve_forever()
except KeyboardInterrupt:
  httpd.shutdown()
  
