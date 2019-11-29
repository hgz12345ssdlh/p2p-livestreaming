#!/usr/bin/python


import sys
import os
import time
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController, OVSSwitch
from mininet.util import dumpNodeConnections
from topo import LivestreamingSingleTopo


ROOT_DIR = os.path.abspath(os.path.dirname(sys.argv[0])) + "/.."
OUTPUT_DIR = ROOT_DIR + "/output"
KEY = "6829proj"


def _launch_service(net):
    """
    Launch the CDN service (an Nginx RTMP server).
    """
    hs = net.get('hs')
    hs.cmd('nginx')
    time.sleep(1)   # Ensure correct startup.


def _do_livestreaming(net, video_file, num_frames):
    """
    Perform full livestreaming procedure.

    Args:
        video_file: Name of the video file to broadcast.
        num_frames: Number of frames in that video file. Note that the viewer
                    `mplayer` will be set to pull num_frames-40 frames. Don't
                    know why but it seems to miss >= 12 frames every time.
    """
    hb, hs, hv = net.get('hb', 'hs', 'hv1')
    # Launch broadcaster & start the streaming.
    print "Broadcaster UP: streaming video file \'%s\'" % (video_file,)
    hb.cmd("python %s/src/hosts/broadcaster.py %s %s %s &" %
           (ROOT_DIR, video_file, hs.IP(), KEY))
    # Launch the viewer.
    print "Viewer 1 UP: %d (-40) frames, make sure it matches the video file" % (num_frames,)
    hv.cmd("python %s/src/hosts/viewer.py %d %s %s" %
           (ROOT_DIR, num_frames-40, hs.IP(), KEY))
    print "Livestreaming FINISH ;)"


def _parse_delay():
    """
    Parse delay in milliseconds, assuming correct logging.
    """
    with open(OUTPUT_DIR+"/hb.log") as fb, open(OUTPUT_DIR+"/hv.log") as fv:
        tb = int([l.strip() for l in fb.read().split('\n') if l][-1])
        tv = int([l.strip() for l in fv.read().split('\n') if l][-1])
        return tv - tb


def livestremaing_test(video_file, num_frames):
    """
    Create a livestreaming topology and run a delay test.
    """
    topo = LivestreamingSingleTopo(num_viewers=1)
    net = Mininet(topo=topo, link=TCLink, controller=RemoteController,
                  switch=OVSSwitch, autoSetMacs=True)
    net.start()
    print "(ignore the above controller warning on port :6653)"
    # Dump the topology.
    print "### Topology ###"
    dumpNodeConnections(net.hosts)
    # Test connectivity. This "pingall" test also gives the L2 learning switch a
    # chance to pre-learn the MAC-port mapping.
    print "### Ping all ###"
    net.pingAll()
    # Launch the nodes apps to perform a live streaming test.
    print "### Live streaming ###"
    _launch_service(net)
    _do_livestreaming(net, video_file, num_frames)
    # Parse the delay from the two logs 'output/hb.log', 'output/hv.log'.
    print "### Results ###"
    print "Approximate delay = %d ms" % (_parse_delay(),)
    net.stop()


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    assert len(sys.argv)==3
    video_file, num_frames = sys.argv[1], int(sys.argv[2])
    livestremaing_test(video_file, num_frames)