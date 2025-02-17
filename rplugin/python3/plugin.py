import pynvim


@pynvim.plugin
class HelloWorld(object):
    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.command("Hello")
    def hello_world(self):
        self.nvim.command('echo "Hello World"')
