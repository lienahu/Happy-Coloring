"""Validate relative resources beneath a GitHub-Pages-style project subpath.
This uses Python HTTP clients, NOT an iOS browser or native photo picker.
"""
from pathlib import Path
from functools import partial
from urllib.request import urlopen
from urllib.parse import urljoin,urlsplit
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import threading,json,hashlib,re,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 results=[]
 with tempfile.TemporaryDirectory() as temp:
  project=Path(temp)/'Happy-Coloring';project.mkdir()
  for f in ['index.html','style.css','apple-colorful.css','languages.css','save-picture.css','app.js','canvas-zoom.js','mobile-ui.js','i18n.js','save-picture.js']:shutil.copy2(ROOT/f,project/f)
  shutil.copytree(ROOT/'assets',project/'assets')
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=temp));threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   base=f'http://127.0.0.1:{server.server_port}/Happy-Coloring/'
   with urlopen(base,timeout=5) as response:
    html=response.read().decode();assert response.status==200
   refs=re.findall(r'(?:src|href)="([^\"]+\.(?:css|js)(?:\?[^\"]*)?)"',html)
   refs += [f'assets/coloring-pages/{n}.png' for n in ['unicorn','princess','cat','butterfly','dinosaur']]
   for ref in refs:
    with urlopen(urljoin(base,ref),timeout=5) as response:
     body=response.read();mime=response.headers.get_content_type()
     path=urlsplit(ref).path;expected=(ROOT/path).read_bytes()
     assert body==expected,(ref,'bytes mismatch')
     if path.endswith('.png'):assert mime=='image/png'
     results.append({'resource':ref,'status':response.status,'mime':mime,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'equal_to_packaged_file':True})
  finally:server.shutdown();server.server_close()
 out=ROOT/'evidence/templates/http-resources.json';out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps({'client':'Python urllib, not browser','project_subpath':'/Happy-Coloring/','resources':results},indent=2))
 print('PASS:',len(results),'runtime/PNG resources served with exact bytes from project subpath')
if __name__=='__main__':main()
