
class TemplateManager():
	templates = {}
	vars = {}
	def add(self, name, file):
		self.templates[name] = open(file, "r").read()
	
	def get(self, name):
		return self.templates[name]
