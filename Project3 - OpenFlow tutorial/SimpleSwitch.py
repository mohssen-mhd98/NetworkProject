from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()


class Tutorial(object):
    """
    A Tutorial object is created for each switch that connects.
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)

        # Use this table to keep track of which ethernet address is on
        # which switch port (keys are MACs, values are ports).
        self.mac_to_port = {}
        #
        # routing_table = [['10.0.1.100/24', '10.0.1.100', 's1-eth1', '10.0.1.1', 1],
        #                  ['10.0.2.100/24', '10.0.2.100', 's1-eth2', '10.0.2.1', 3],
        #                  ['10.0.3.100/24', '10.0.3.100', 's1-eth3', '10.0.3.1', 2]]

    def resend_packet(self, packet_in, out_port):
        """
        Instructs the switch to resend a packet that it had sent to us.
        "packet_in" is the ofp_packet_in object the switch had sent to the
        controller due to a table-miss.
        """
        msg = of.ofp_packet_out()
        msg.data = packet_in

        # Add an action to send to the specified port
        action = of.ofp_action_output(port=out_port)
        msg.actions.append(action)

        # Send message to switch
        self.connection.send(msg)

    def act_like_hub(self, packet, packet_in):
        """
        Implement hub-like behavior -- send all packets to all ports besides
        the input port.
        """

        # We want to output to all ports -- we do that using the special
        # OFPP_ALL port as the output port.  (We could have also used
        # OFPP_FLOOD.)
        self.resend_packet(packet_in, of.OFPP_ALL)

        # Note that if we didn't get a valid buffer_id, a slightly better
        # implementation would check that we got the full data before
        # sending it (len(packet_in.data) should be == packet_in.total_len)).

    def act_like_switch(self, packet, packet_in):
        """
        Implement switch-like behavior.
        """

        # Learn the port for the source MAC
        in_port = packet_in.in_port
        dl_src = str(packet.src)
        dl_dst = str(packet.dst)
        self.mac_to_port[dl_src] = in_port

        if dl_dst in self.mac_to_port:
            # Send packet out the associated port
            dst_in_port = self.mac_to_port[dl_dst]
            self.resend_packet(packet_in, dst_in_port)

            # Once you have the above working, try pushing a flow entry
            # instead of resending the packet (comment out the above and
            # uncomment and complete the below.)

            log.debug(
                "Installing flow for mac address {} on port {}. Destination mac is {}".format(dl_src, in_port, dl_dst))
            # Maybe the log statement should have source/destination/port?

            msg = of.ofp_flow_mod()

            # Set fields to match received packet
            # msg.match = of.ofp_match.from_packet(packet)
            msg.match = of.ofp_match.from_packet(packet)

            # < Set other fields of flow_mod (timeouts? buffer_id?) >

            # < Add an output action, and send -- similar to resend_packet() >
            action = of.ofp_action_output(port=dst_in_port)
            msg.actions.append(action)

            # log.debug(msg)
            self.connection.send(msg)

        else:
            # Flood the packet out everything but the input port
            # This part looks familiar, right?
            self.resend_packet(packet_in, of.OFPP_ALL)

    def _handle_PacketIn(self, event):
        """
        Handles packet in messages from the switch.
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.

        # Comment out the following line and uncomment the one after
        # when starting the exercise.
        # self.act_like_hub(packet, packet_in)
        self.act_like_switch(packet, packet_in)


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Tutorial(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
