"""Verify actual HTTP bytes under the GitHub Pages style /Happy-Coloring/ prefix.
This is a Python HTTP test, NOT a browser networking or Safari test.
"""
from pathlib import Path
import functools,http.server,threading,urllib.request,urllib.parse,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path.startswith('/Happy-Coloring/'):
   self.path=self.path[len('/Happy-Coloring'):]
  else:self.send_error(404);return
  super().do_GET()
def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 base=f'http://127.0.0.1:{server.server_port}/Happy-Coloring/'
 html=(ROOT/'index.html').read_text();urls=['index.html']+re.findall(r'(?:src|href)="([^"<>]+\.(?:js|css)(?:\?[^"<>]*)?)"',html)+['assets/template-library/catalog.json?v=1']
 catalog=json.loads((ROOT/'assets/template-library/catalog.json').read_text());urls+=list(dict.fromkeys(i[k] for i in catalog['items'] for k in ['src','thumb']))
 records=[]
 try:
  for url in urls:
   with urllib.request.urlopen(base+url) as r:data=r.read();status=r.status
   file=ROOT/urllib.parse.urlsplit(url).path
   assert status==200 and data==file.read_bytes(),url
   records.append({'path':url,'status':status,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 finally:server.shutdown();server.server_close()
 out=ROOT/'evidence/fill-library';out.mkdir(parents=True,exist_ok=True);(out/'http-resources.json').write_text(json.dumps(records,indent=2));print(f'{len(records)} resources returned HTTP 200 and exact bytes')
if __name__=='__main__':main()
