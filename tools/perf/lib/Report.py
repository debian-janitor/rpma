#!/usr/bin/env python3
#
# SPDX-License-Identifier: BSD-3-Clause
# Copyright 2021, Intel Corporation
#

#
# Report.py -- a report object (EXPERIMENTAL)
#

import os

from .Part import *

class Report:
    """A report object"""

    def _load_parts(self, loader, env, bench):
        variables = self.config['report']
        if 'authors' in variables:
            variables['authors'] = "\n".join(['- ' + author for author in variables['authors']])

        # XXX type validation is missing
        if 'configuration' not in variables:
            raise SyntaxError("config.json misses ['report']['configuration'] entry")
        else:
            if 'common' not in variables['configuration']:
                raise SyntaxError("config.json misses ['report']['configuration']['common'] entry")
            if 'target' not in variables['configuration']:
                raise SyntaxError("config.json misses ['report']['configuration']['target'] entry")
            if 'bios' not in variables['configuration']:
                raise SyntaxError("config.json misses ['report']['configuration']['bios'] entry")
            else:
                if 'settings' not in variables['configuration']['bios']:
                    raise SyntaxError("config.json misses ['report']['configuration']['bios']['settings'] entry")
                if 'excerpt' not in variables['configuration']['bios']:
                    raise SyntaxError("config.json misses ['report']['configuration']['bios']['excerpt'] entry")

        # the only correct type is 'kvtable'
        variables['configuration']['common']['type'] = 'kvtable'
        variables['configuration']['target']['type'] = 'kvtable'
        variables['configuration']['bios']['settings']['type'] = 'kvtable'
        variables['configuration']['bios']['excerpt']['type'] = 'kvtable'

        preamble = Part(loader, env, 'preamble')
        preamble.process_variables_level(variables, {})
        preamble.set_variables(variables)
        self.parts = [preamble]
        for partname in bench.parts:
            part = Part(loader, env, partname)
            part.set_variables({'figure': self.figures})
            self.parts.append(part)

    def _load_figures(self, bench):
        self.figures = {}
        for f in bench.figures:
            html = f.to_html()
            # add to 2-level figure dictionary
            if f.file not in self.figures.keys():
                self.figures[f.file] = {}
            self.figures[f.file][f.key] = html

    def __init__(self, loader, env, bench):
        self.env = env # jinja2.Environment
        self.config = bench.config
        self.result_dir = bench.result_dir
        self._load_figures(bench)
        self._load_parts(loader, env, bench)

    def _create_menu(self):
        return "".join([part.menu() for part in self.parts])

    def _create_content(self):
        return "".join([part.content() for part in self.parts])

    def _create_header(self):
        # XXX both *_header.md files can be integrated directly into
        # the layout.html file so this step won't be necessary
        tmpl = self.env.get_template('report_header.md')
        md = tmpl.render(self.config['report'])
        html = markdown2.markdown(md)
        return html

    def create(self, output):
        """Generate a report and write it to the output file"""
        variables = {}
        variables['menu'] = self._create_menu()
        variables['header'] = self._create_header()
        variables['content'] = self._create_content()
        # render the report with the complete layout
        layout_tmpl = self.env.get_template('layout.html')
        html = layout_tmpl.render(variables)
        # write the output file
        output_file = os.path.join(self.result_dir, output + '.html')
        with open(output_file, 'w') as f:
            f.write(html)
