#!/usr/bin/env python

#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import pydot
import subprocess
import sys

if len(sys.argv) < 3:
    sys.stderr.write('Usage: sys.argv[0] <in> <out>\n')
    sys.exit(1)

infilename = sys.argv[1]
outfilename = sys.argv[2]

print('reading graph from "%s"' % outfilename)
print('writing graph to "%s"' % outfilename)

def read_edges(g, fname):
    f = open(fname, 'r')
    for line in f.readlines():
        src_name, dst_name = line.split()
        g.add_edge(pydot.Edge(src_name, dst_name))
    f.close()

    return g

def read_as_info(g, fname):
    as_info = {}

    f = open(fname, 'r')
    for line in f.readlines():
        node_name, asn = line.split()
        if not asn in as_info:
            as_info[asn] = pydot.Subgraph()
        as_info[asn].add_node(pydot.Node(node_name))
    f.close()

    for subgraph in as_info.values():
        g.add_subgraph(subgraph)

    return g

def read_graph(fname):
    g = pydot.graph_from_edges([])

    #g = read_as_info(g, '%s.as_info' % fname)
    g = read_edges(g, '%s.edges' % fname)

    return g

def write_graph(graph, fname):
    f = open(fname, 'w')

    for node in graph.get_nodes():
        if node.get_name() == 'node':
            continue

        if node.get_name() == 'graph':
            continue

        line = [node.get_name()]
        line.extend(node.get_pos().strip('"').split(','))
        line = '%s\n' % ' '.join(line).strip()

        f.write(line)
    f.close()

def layout_graph(graph, fname):
    print('writing un-layouted graph to "%s.dot"' % fname)

    graph.set_overlap('scale')
    dot = graph.create_dot()
    f = open('%s.dot' % fname, 'w')
    f.write(dot)
    f.close()

    neato_dot = subprocess.check_output(['/usr/bin/neato', '-Tdot', '%s.dot' % fname])
    neato_png = subprocess.check_output(['/usr/bin/neato', '-Tpng', '%s.dot' % fname])
    neato_pdf = subprocess.check_output(['/usr/bin/neato', '-Tpdf', '%s.dot' % fname])
    print('writing layouted graph to "%s.dot.layouted.dot"' % fname)
    f = open('%s.dot.layouted.dot' % fname, 'w')
    f.write(neato_dot)
    f.close()
    print('writing layouted graph to "%s.dot.png"' % fname)
    f = open('%s.dot.png' % fname, 'w')
    f.write(neato_png)
    f.close()
    print('writing layouted graph to "%s.dot.pdf"' % fname)
    f = open('%s.dot.pdf' % fname, 'w')
    f.write(neato_pdf)
    f.close()

    print('re-reading layouted dot from internal variable')
    graph = pydot.graph_from_dot_data(neato_dot)
    return graph

# read graph
g = read_graph(infilename)

# layout graph
g = layout_graph(g, outfilename)

# write graph
print('writing graph to "%s.dotout"' % outfilename)
write_graph(g, '%s.dotout' % outfilename)
