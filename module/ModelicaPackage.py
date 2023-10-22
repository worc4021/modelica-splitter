from typing import Any, List
import re
import logging

class ModelicaClass:
    name : str
    parent : 'ModelicaClass'
    children : List['ModelicaClass']
    body : str
    classtype : str
    partial : str

    def __init__(self, text: str, parent : 'ModelicaClass' = None):
        self.parent = parent
        text = text.strip()

        self.children = []
        if parent:
            class_pattern = re.compile(r'\s*(?P<partial>partial|\s*)\s*(?P<childtype>package|model|class|block|record|function|connector)\s+(?P<childname>[A-Za-z0-9]+)\b')
        else:
            class_pattern = re.compile(r'\s*(?P<childtype>package)\s+(?P<childname>\S+)\b')

        class_match = class_pattern.search(text)
        if class_match:
            self.name = class_match.group("childname")
            end_pattern = re.compile(r'\s+end\s+{};'.format(self.name))
            end_match = end_pattern.search(text)
            if end_match:
                self.body = text[class_match.end():end_match.start()]
                self.classtype = class_match.group("childtype")
                if parent:
                    self.partial = class_match.group("partial")
                else:
                    self.partial = ''
                

    def __call__(self):
        if self.classtype == 'package':

            child_pattern = re.compile(r'\s*(?P<partial>partial|\s*)\s*(?P<childtype>package|model|class|block|record|function|connector)\s+(?P<childname>[A-Za-z0-9]+)\b')
            first = 0
            child_match = child_pattern.search(self.body[first:])
            while child_match:
                if child_match.group("childname") in ['for', 'while', 'if']:
                    first+=child_match.end()
                elif child_match.group("childtype") == 'connector':
                    alias_pattern = re.compile(r'connector\s*{}\s*='.format(child_match.group("childname")))
                    alias_match = alias_pattern.search(self.body[first:])
                    if alias_match:
                        first+=child_match.end()
                    else:
                        first = self.match_helper(child_match, first)
                else:
                    first = self.match_helper(child_match, first)

                child_match = child_pattern.search(self.body[first:])

            for child in self.children:
                child()
        else:
            pass

    def match_helper(self, child_match, first):
        end_pattern = re.compile(r'\s+end\s+{};'.format(child_match.group("childname")))
        nmatches = len(end_pattern.findall(self.body[first:]))
        if nmatches > 1:
            offset = 0
            for i in range(nmatches-1):
                end_match = end_pattern.search(self.body[first+offset:])
                offset=end_match.end()
            end_match = end_pattern.search(self.body[first+offset:])
            last = first+offset+end_match.end()
        else:
            end_match = end_pattern.search(self.body[first:])
            if end_match:
                last = first+end_match.end()


        if end_match:
            child = ModelicaClass(self.body[first+child_match.start():last], self)
            self.children.append(child)
            logging.info(f'Found child {child_match.group("childname")} and child found {child.name}')
            self.body = self.body.replace(self.body[first+child_match.start():last], '')
        else:
            first+=child_match.end()
        return first


    def save(self, path: str):
        from os.path import join
        from os import makedirs

        if self.classtype == 'package':
            makedirs(join(path, self.name), exist_ok=True)
            order = [c.name for c in self.children]
            with open(join(path, self.name, 'package.order'), 'w') as f:
                f.write('\n'.join(order))

            if self.parent:
                parent_string = f'within {self.parent.name};'
            else:
                parent_string = ''
            
            lines = [parent_string, f'package {self.name}']
            lines+=self.body.splitlines()
            lines.append(f'end {self.name};')
            with open(join(path, self.name, 'package.mo'), 'w') as f:
                f.write('\n'.join(lines))
            
            for child in self.children:
                child.save(join(path, self.name))
        else:
            lines = [f'{self.partial} {self.classtype} {self.name}']
            lines+= self.body.splitlines()
            lines.append(f'end {self.name};')

            with open(join(path, f'{self.name}.mo'), 'w') as f:
                f.write('\n'.join(lines))