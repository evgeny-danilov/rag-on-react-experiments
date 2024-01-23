import re
import os
import pdb
import subprocess

from langchain_core.output_parsers import StrOutputParser


AllowedCommands = ['git', 'flask', 'pip', 'python', 'alembic', 'date', 'pytest', './run_tests.sh']
BlockedCommands = ['git rm', 'git reset', 'git push --force', 'flask db drop']

# 'git clean -f && git restore .' - revert all changes in git

class CommandRunner:
    def __init__(self, directory, llm=None):
        self.directory = directory.strip('/')
        self.full_directory_path = os.path.abspath(os.path.join(os.curdir, self.directory))
        self.llm = llm

    def invoke(self, command):
        command = command.strip(" `'\n")

        if self._is_invalid_command(command):
            return [f"Command <{command}> not allowed by custom security reasons. Allowed: {AllowedCommands}, Blocked: {BlockedCommands}", None]

        result = self._run_command(command)
        if self.llm is not None and result.stderr:
            corrected_command = self._command_self_correction(command=command, error_message=result.stderr)
            result = self._run_command(corrected_command)
        return result.stdout, result.stderr

    def _is_invalid_command(self, command):
        if not any(command.startswith(allowed) for allowed in AllowedCommands) or \
                any(command.startswith(blocked) for blocked in BlockedCommands):
            return True

    def _run_command(self, command):
        command = command.strip(" `'\n")
        # TODO: check if there is a folder venv, and create it if not exist, along with vend added in .gitignore
        command = f'source {self.full_directory_path}/venv/bin/activate && {command}'

        return subprocess.run(command, shell=True, text=True, cwd=self.directory,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _command_self_correction(self, command, error_message):
        prompt = f"Correct bash command:```bash\n{command}\n```\n\nDo not add additional explanation. Take into account error:\n{error_message}\n\nOutput template:\n```bash\nflask db\n```"
        chain = self.llm | StrOutputParser()
        llm_answer = chain.invoke(prompt)
        cleaned_command = re.sub(r'^```[a-z]*\n', '', llm_answer, flags=re.MULTILINE).strip('`\n')

        return cleaned_command


if __name__ == '__main__':
    project_dir = '../_test_projects/jde-coffee'
    stdout, stderr = CommandRunner(directory=project_dir).invoke('pip3 list | grep zip')
    print("Standard Output:", stdout)
    print("Standard Error:", stderr)
