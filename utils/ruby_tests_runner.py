import subprocess

class RubyTestsRunner:
    def __init__(self, directory, ruby_version='3.2.2'):
        self.directory = directory
        self.ruby_version = ruby_version

    def invoke(self, *args, **kwargs):
        command = f'rvm {self.ruby_version} do bundle exec rspec'
        result = subprocess.run(command, cwd=self.directory, shell=True, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout

if __name__ == '__main__':
    project_dir = "../_test_projects/flight-service/api/"
    ruby_version = "3.2.2"
    stdout = RubyTestsRunner(directory=project_dir, ruby_version=ruby_version).invoke()
    print("Standard Output:", stdout)
