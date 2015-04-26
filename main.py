import cherrypy
import os
import subprocess
import cgi
from StringIO import StringIO
import zipfile
from cherrypy.lib.static import serve_file

cwd=os.getcwd()
filesPath="files"

#this is unsafe - only for debug usage
#filesPath="."

def main():
	cherrypy.tree.mount(PageBase(), '/')
	cherrypy.tree.mount(PageScriptService(), '/scriptservice')
	cherrypy.tree.mount(PageFiles(), '/files')
	cherrypy.tree.mount(PageImport(), '/import')
	cherrypy.tree.mount(PageFolders(), '/folders')
	cherrypy.tree.mount(PageStatic(), '/static', { '/' : {
		'tools.staticdir.on': True,
		'tools.staticdir.dir': cwd+"/static"
	}})

	cherrypy.config.update({
	    'server.socket_host': '0.0.0.0',
		'server.socket_port': 8080
	})
	cherrypy.engine.start()
	cherrypy.engine.block()


scriptProcess = None
class PageScriptService(object):
    def _cp_dispatch(self, vpath):
        cherrypy.request.params['path'] = '/'.join(vpath)
        vpath[:] = []
        return self
	
    @cherrypy.expose
    def index(self, path=None):
        global scriptProcess;
        
    	if cherrypy.request.method == 'DELETE':
    	    if scriptProcess is None:
    	        raise cherrypy.HTTPError(503)
    	    os.kill(scriptProcess.pid, 15)
    	if cherrypy.request.method == 'GET':
    	    if scriptProcess is None:
    	        raise cherrypy.HTTPError(503)
    	    result = StringIO()
    	    while True:
                out = scriptProcess.stderr.read(1)
                if out == '' and scriptProcess.poll() != None:
                    break
                if out != '':
                    result.write(out)
            result.close()
            if not os.kill(scriptProcess.pid, 0):
                scriptProcess = None
            return result.getvalue()
    	elif cherrypy.request.method == 'PUT':
    	    if scriptProcess is None:
    		abspath = os.path.abspath(filesPath+"/"+path)
    		if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
    		    raise cherrypy.HTTPError(403, 'Not allowed to run %s' % (path))
                scriptProcess = subprocess.Popen('sh -c "cd files; python2 %s"' % (abspath), shell=True, stderr=subprocess.PIPE)
    	return ''
 
# See http://tools.cherrypy.org/wiki/DirectToDiskFileUpload
class myFieldStorage(cgi.FieldStorage):
    """Our version uses a named temporary file instead of the default
    non-named file; keeping it visibile (named), allows us to create a
    2nd link after the upload is done, thus avoiding the overhead of
    making a copy to the destination filename."""
    def make_file(self, binary=None):
        return tempfile.NamedTemporaryFile()

def noBodyProcess():
    cherrypy.request.process_request_body = False
cherrypy.tools.noBodyProcess = cherrypy.Tool('before_request_body', noBodyProcess)

class PageImport(object):
	def _cp_dispatch(self, vpath):
		cherrypy.request.params['path'] = '/'.join(vpath)
		vpath[:] = []
		return self
	
        @cherrypy.expose
        @cherrypy.tools.noBodyProcess()
	def index(self, path=None):
		if cherrypy.request.method == 'POST':
			if not path:
				raise cherrypy.HTTPError(400)
			abspath = os.path.abspath(filesPath+"/"+path)
			if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'Not allowed to import at %s' % (path))
			if os.path.exists(abspath) and not os.path.isdir(abspath):
				raise cherrypy.HTTPError(409, '%s is not a directory' % (path))
                        cherrypy.response.timeout = 3600
                        lcHDRS = {}
                        for key, val in cherrypy.request.headers.iteritems():
                            lcHDRS[key.lower()] = val

			infile = StringIO()
			cl = cherrypy.request.headers['Content-Length']
                        formFields = myFieldStorage(fp=cherrypy.request.rfile,
                                    headers=lcHDRS,
                                    environ={'REQUEST_METHOD':'POST'},
                                    keep_blank_values=True)
                        theFile = formFields['files[]']
			with zipfile.ZipFile(theFile.file, "r") as f:
			  f.extractall(abspath)
		return ''

class PageFolders(object):
	def _cp_dispatch(self, vpath):
		cherrypy.request.params['path'] = '/'.join(vpath)
		vpath[:] = []
		return self

	@cherrypy.expose
	def index(self, path=None):
		if cherrypy.request.method == 'GET':
			if not path:
				path = ''
			abspath = os.path.abspath(filesPath+"/"+path)
			if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'Not allowed to list files at %s' % (path))
			res=[]
			for name in os.listdir(abspath):
				currentFile = abspath+"/"+name
				fileType='u';
				if (os.path.isdir(currentFile)):
					fileType='d';
				elif (os.path.isfile(currentFile)):
					fileType='f';
				res.append(fileType+str(name))
			return '\r\n'.join(res)
		elif cherrypy.request.method == 'PUT':
			if not path:
				raise cherrypy.HTTPError(400)
			abspath = os.path.abspath(filesPath+"/"+path)
			if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'Not allowed to create folder at %s' % (path))
			if (os.path.exists(abspath)):
				raise cherrypy.HTTPError(409, 'A file or folder at %s already exists' % (path))
			os.mkdir(abspath)
		elif cherrypy.request.method == 'DELETE':
			if not path:
				raise cherrypy.HTTPError(400)
			abspath = os.path.abspath(filesPath+"/"+path)
			if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'The path %s may not be deleted' % (path))
			if not os.path.exists(abspath):
				raise cherrypy.HTTPError(409, 'A file or folder at %s does not exist' % (path))
			if os.path.isdir(abspath):
				os.rmdir(abspath)
			elif os.path.isfile(abspath):
				os.remove(abspath)
		return ''

class PageFiles(object):
	def _cp_dispatch(self, vpath):
		cherrypy.request.params['file'] = '/'.join(vpath)
		vpath[:] = []
		return self

	def touch(self, fname, times=None):
		print('==='+fname)
		with open(fname, 'a') as f:
			os.utime(fname, times)

	@cherrypy.expose
	def index(self, file=None):
		if cherrypy.request.method == 'GET':
			if not file:
				file = ''
			abspath = os.path.abspath(filesPath+"/"+file)
			print("=====  " + abspath)
			if (filesPath == '.' or abspath.startswith(cwd+"/"+filesPath)):
				if (os.path.isfile(abspath)):
					return serve_file(abspath)
				if (os.path.isdir(abspath)):
					cherrypy.response.headers['Content-Type'] = 'application/zip'
					cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="%s"' % ('download.zip')
					output = StringIO()
					file = zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED)
					for root,subfolders,files in os.walk(abspath):
						for f in files:
							filePath = os.path.join(root,f)
							relPath = os.path.relpath(filePath, abspath)
							file.write(filePath, relPath)
					file.close()
					return output.getvalue()
		elif cherrypy.request.method == 'POST':
			if not file:
				raise cherrypy.HTTPError(400)
			abspath = os.path.abspath(filesPath+"/"+file)
			if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'Not allowed to create folder at %s' % (file))
			if os.path.exists(abspath) and not os.path.isfile(abspath):
				raise cherrypy.HTTPError(409, '%s is not a file' % (file))
			cl = cherrypy.request.headers['Content-Length']
			data = cherrypy.request.body.read(int(cl))
			with open(abspath, 'w') as f:
				f.write(data)
		elif cherrypy.request.method == 'PUT':
			if not file:
				raise cherrypy.HTTPError(400)
			abspath = os.path.abspath(filesPath+"/"+file)
			if filesPath != '.'and  not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'Not allowed to create folder at %s' % (file))
			if os.path.exists(abspath):
				raise cherrypy.HTTPError(409, 'A file or folder at %s already exists' % (file))
			self.touch(abspath)
		elif cherrypy.request.method == 'DELETE':
			if not file:
				raise cherrypy.HTTPError(400)
			abspath = os.path.abspath(filesPath+"/"+file)
			if filesPath != '.' and not abspath.startswith(cwd+"/"+filesPath):
				raise cherrypy.HTTPError(403, 'The path %s may not be deleted' % (file))
			if not os.path.exists(abspath):
				raise cherrypy.HTTPError(409, 'A file or folder at %s does not exist' % (file))
			if os.path.isdir(abspath):
				os.rmdir(abspath)
			elif os.path.isfile(abspath):
				os.remove(abspath)
		return ''

class PageStatic(object):
	pass
""" @cherrypy.expose
	def download(self, filepath):
		return serve_file(filepath, "application/x-download", "attachment")
"""

class PageBase(object):
	def index(self):
		#page = t.get('index')
		#return page
		return serve_file(cwd+"/templates/index.html")
	index.exposed = True

if __name__ == '__main__':
	main();
