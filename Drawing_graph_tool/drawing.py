from graph_tool.all import *



g = Graph()
v1 = g.add_vertex()
v2 = g.add_vertex()
v3 = g.add_vertex()
v4 = g.add_vertex()
v5 = g.add_vertex()
v6 = g.add_vertex()
v7 = g.add_vertex()
v8 = g.add_vertex()
'''
v9 = g.add_vertex()
v10 = g.add_vertex()
v12 = g.add_vertex()
v13 = g.add_vertex()
v14 = g.add_vertex()
v15 = g.add_vertex()
v16 = g.add_vertex()
v17 = g.add_vertex()
v18 = g.add_vertex()
'''
e = g.add_edge(v1, v2)
e = g.add_edge(v1, v3)
e = g.add_edge(v1, v4)
e = g.add_edge(v1, v5)
e = g.add_edge(v5, v6)
e = g.add_edge(v2, v7)
e = g.add_edge(v3, v8)
e = g.add_edge(v2, v8)
e = g.add_edge(v5, v8)
e = g.add_edge(v4, v5)
'''e = g.add_edge(v3, v3)
e = g.add_edge(v8, v2)
e = g.add_edge(v4, v3)
e = g.add_edge(v12, v4)
e = g.add_edge(v17, v5)
e = g.add_edge(v10, v6)
e = g.add_edge(v12, v7)
e = g.add_edge(v13, v8)
e = g.add_edge(v1, v8)
e = g.add_edge(v18, v8)
e = g.add_edge(v8, v5)
e = g.add_edge(v12, v3)
'''
vprop = g.new_vertex_property("string")
vprop[v1] = 'Jessi'
vprop[v2] = 'Frenci'
g.vertex_properties["name"]=vprop
vpropc = g.new_vertex_property("vector<float>")
vpropc[v1] = [0.640625, 0.2, 0, 0.9]
vpropc[v2] = [1, 1, 0.2, 0.9]
g.vertex_properties["color"]=vpropc
graph_draw(g, vertex_text=g.vertex_properties["name"], vertex_font_size=18, output_size=(800, 800),
           vertex_fill_color= g.vertex_properties["color"],output="more_nodes.png")