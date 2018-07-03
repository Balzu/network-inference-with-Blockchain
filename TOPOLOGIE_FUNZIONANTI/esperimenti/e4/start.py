#!/us5/bin/python

from create_merge_topo import *

def run():
    os.system('./clean.sh')  # Delete previously generated files..
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    compute_distances(net) 
    make_anonymous_and_blocking_routers(net)
    create_traces(net)
    alias = create_alias()
    (vtopo, traces) = create_virtual_topo_and_traces(alias, net)
    print_topo(vtopo)
    print_nodes(vtopo)
    print_traces(traces)
    (M,C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    print_topo(mtopo)
    net.stop()
    

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
