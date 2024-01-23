import collections
import subprocess
import os


class GitFilesLister:
    def __init__(self, directory):
        if not os.path.isdir(directory):
            raise ValueError(f"Directory '{directory}' does not exist.")
        self.directory = directory
        self.max_depth = None

    def list_files(self, rel_path='', max_depth=None):
        self.max_depth = max_depth
        rel_path = rel_path.strip(" '/")
        if rel_path == '':
            output = subprocess.check_output(['git', '-C', self.directory, 'ls-files', '--cached', '--others', '--exclude-standard']).decode().splitlines()
        else:
            output = subprocess.check_output(['git', '-C', self.directory, 'ls-files', '--cached', '--others', '--exclude-standard', rel_path]).decode().splitlines()

        if len(output) > 0:
            filtered_output = [line for line in output if not os.path.basename(line).startswith('.')]
            file_tree = self._build_file_tree(filtered_output)
            return "\n" + self._tree_to_string(file_tree)
        else:
            return f'Directory is empty or does not exist'

    def _build_file_tree(self, file_paths):
        tree = lambda: collections.defaultdict(tree)
        root = tree()
        for path in file_paths:
            self._add_to_tree(root, path.split('/'))
        return root

    def _add_to_tree(self, tree, nodes):
        for node in nodes:
            tree = tree[node]

    def _tree_to_string(self, tree, level=0):
        if self.max_depth is not None and level > self.max_depth:
            return ""
        tree_string = ""
        for name, subtree in tree.items():
            tree_string += (' ' * level * 2) + '- ' + name + '\n'
            if isinstance(subtree, collections.defaultdict):
                tree_string += self._tree_to_string(subtree, level + 1)
        return tree_string


if __name__ == '__main__':
    path = "../_test_projects/jde-coffee/"
    lister = GitFilesLister(path)
    file_tree_string = lister.list_files('', max_depth=2)
    print(file_tree_string)
