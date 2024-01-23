import os
import time
import pdb

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser

from neo.neo_writter import NeoWritter
from py2neo import Graph, Node, Relationship


class FoldersStructure:
    def __init__(self, directory, include_files=False, max_depth=None, create_graph=False):
        self.directory = directory
        self.include_files = include_files
        self.max_depth = max_depth
        self.create_graph = create_graph
        self.graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"), name='enedis')

    def parse(self, path):
        path = path.strip(" '/")
        if path in ['', 'N/A', 'None', '/']:
            path = self.directory
        else:
            path = os.path.join(self.directory, path)
        if self.create_graph:
            self._run_graph_creation(path)
        return f"Path: {path}\n" + self._recursive_list(path)

    def _recursive_list(self, path, level=0):
        if self.max_depth and level == self.max_depth:
            return ''
        output = ''
        for item in os.listdir(path):
            if item.startswith('.'):  # ignore hidden directories
                continue
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                sub_items = os.listdir(item_path)
                file_count = sum(os.path.isfile(os.path.join(item_path, sub_item)) for sub_item in sub_items)
                if file_count > 0 and not any(os.path.isdir(os.path.join(item_path, sub_item)) for sub_item in sub_items):
                    output += f"{'  ' * level}- {item} ({file_count} files)\n"
                else:
                    output += f"{'  ' * level}- {item}\n"
                output += self._recursive_list(path=item_path, level=(level + 1))
            elif self.include_files and os.path.isfile(item_path):
                output += f"{'  ' * level}- {item}\n"

        return output

    def _run_graph_creation(self, path):
        total_items = sum(
            len([d for d in dirs if not d.startswith('.')]) + len([f for f in files if not f.startswith('.')]) for
            _, dirs, files in os.walk(path))
        item_count = 0

        for root, dirs, files in os.walk(path):
            # Exclude hidden directories and files
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

            # Create or get a node for the root
            root_node_path = root.replace(self.directory, '').lstrip('/')
            root_node = self.graph.nodes.match("Directory", path=root_node_path).first()

            for name in dirs + files:
                # Determine the type (Directory or File)
                item_type = "Directory" if name in dirs else "File"

                # Create or get a node for the item
                file_path = os.path.join(root, name).replace(self.directory, '').lstrip('/')
                updated_at = time.ctime(os.path.getmtime(os.path.join(root, name)))
                item_node = Node(item_type, name=name, path=file_path, updated_at=updated_at)
                self.graph.merge(item_node, item_type, "path")

                # Create a relationship
                if root_node:
                    rel = Relationship(root_node, "CONTAINS", item_node)
                    self.graph.create(rel)

                item_count += 1
                print(f"\rProgress: {item_count}/{total_items} items processed", end='', flush=True)



folder_structure_template = """
Files structure:
{{ files }}

Question: {{query}}.

Instruction: Highlight exact file names that might help to solve question.
"""

class FoldersStructureAnalyzer:
    def __init__(self, directory, llm):
        self.llm = llm
        self.folder_structure = FoldersStructure(directory=directory)

    def invoke(self, query):
        files = self.folder_structure.list_dirs_and_files(path='/')
        prompt = ChatPromptTemplate.from_template(folder_structure_template, template_format='jinja2')
        chain = prompt | self.llm | StrOutputParser()

        return chain.invoke(input={'query': query, 'files': files})


PREVIEW_LENGTH = 300
class CustomDirectoryLoader:

    def __init__(self, directory):
        self.directory = directory

    def invoke(self, path):
        path = path.strip(" ").strip("'").strip("/")
        docs = DirectoryLoader(path=self.directory, show_progress=True, glob=f'**/{path}/*.*', silent_errors=True).load()

        for document in docs:
            if len(document.page_content) > PREVIEW_LENGTH:
                document.page_content = "[PREVIEW MODE] " + document.page_content[:300] + "...[Read document to see full content]"

        return docs


class CustomUnstructuredFileLoader:
    def __init__(self, directory):
        self.directory = directory

    def invoke(self, path):
        full_path = os.path.join(self.directory, path.strip(" '`"))
        if os.path.isfile(full_path):
            _, file_extension = os.path.splitext(full_path)
            if file_extension.lower() in ['.pdf', '.doc', '.docx', '.xlsx']:
                return [UnstructuredFileLoader(full_path).load()]
            else:
                with open(full_path, 'r') as file:
                    return f"\n```{file_extension}\n{file.read()}\n```\n"
        else:
            return f"Can not find file <{full_path}>"


if __name__ == '__main__':
    project_dir = "../../../enedis/client-artifacts/drive-download-20231023T125422Z-001"
    folder_structure = FoldersStructure(directory=project_dir)
    folder_structure.graph.run("MATCH (n) DETACH DELETE n")
    print("Graph Cleaned")
    folder_structure.parse('')
