import socket
import struct
import textwrap
import numpy
from threading import Thread
import operator

TAB1 = '\t - '
TAB2 = '\t\t - '
TAB3 = '\t\t\t - '
TAB4 = '\t\t\t\t - '

DATA_TAB1 = '\t '
DATA_TAB2 = '\t\t '
DATA_TAB3 = '\t\t\t '
DATA_TAB4 = '\t\t\t\t '


EXIT = False
FRAGMENTED_PACKETS_NUM = 0

# sudo python3 main.py


def main():

    tcp_count = 0
    udp_count = 0
    icmp_count = 0
    other_proto = 0
    fragmented_dict = {}
    dns_count = 0
    http_count = 0
    https_count = 0
    # make a thread that listens for stop messages
    t = Thread(target=stop_sniffing)

    # make the thread daemon so it ends whenever the main thread ends
    t.daemon = True
    # start the thread
    t.start()
    data_list = []
    packet_sent_num = {}
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
    while not EXIT:
        raw_data, addr = conn.recvfrom(65536)
        dest_mac, src_mac, eth_proto, data = ethernet_frame(raw_data)
        data_list.append(len(data)+14)

        print('\nEthernet Frame:')
        print(TAB1 + "Packet Size: {}".format(len(data)))
        print(TAB1 + 'Destination: {}, Source: {}, Protocol: {}'.format(dest_mac, src_mac, eth_proto))

        # 8 for ipv4
        if eth_proto == 8:
            (version, header_length, ttl, proto, src, target, data, fragmented_dict) = ipv4_packet(data, fragmented_dict)

            if target not in packet_sent_num:
                packet_sent_num.update({target: 0})
            else:
                packet_sent_num[target] += 1

            print(TAB1 + 'IPv4 Packet:')
            print(TAB2 + 'Version: {}, Header Length: {}, TTL: {}'.format(version, header_length, ttl))
            print(TAB2 + 'Protocol: {}, Source Address: {}, Destination Address: {}'.format(proto, src, target))

            # ICMP
            if proto == 1:
                icmp_type, code, checksum, data = icmp_packet(data)
                print(TAB1 + 'ICMP Packet:')
                print(TAB2 + 'Type: {}, Code: {}, CheckSum: {},'.format(icmp_type, code, checksum))
                print(TAB2 + 'Data:')
                print(format_multi_line(DATA_TAB3, data))
                icmp_count += 1
                print("-----------------------------------------------------------------------------------------------")

            # TCP
            elif proto == 6:
                (src_port, dest_port, sequence, acknowledgement, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data) = tcp_segment(data)
                print(TAB1 + 'TCP Segment:')
                print(TAB2 + 'Source Port: {}, Destination Port: {}'.format(src_port, dest_port))
                print(TAB2 + 'Sequence num: {}, Acknowledgement: {}'.format(sequence, acknowledgement))
                print(TAB2 + "Flags:")
                print(TAB3 + 'URG: {}, ACK: {}, PSH: {}, RST: {}, SYN: {}, FIN: {}'.format(flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin))

                if src_port == 80 or dest_port == 80:
                    print(TAB2 + 'HTTP: ')
                    http_count += 1
                elif src_port == 443 or dest_port == 443:
                    print(TAB2 + 'HTTPs: ')
                    https_count += 1
                elif src_port == 25 or dest_port == 25:
                    print(TAB2 + 'SMTP: ')
                elif src_port == 53 or dest_port == 53:
                    print(TAB2 + 'DNS: ')
                    dns_count += 1
                elif (src_port == 20 or src_port == 21) or (dest_port == 20 or dest_port == 21):
                    print(TAB2 + 'FTP: ')

                print(TAB3 + 'Data:')
                print(format_multi_line(DATA_TAB4, data))
                print("-----------------------------------------------------------------------------------------------")
                tcp_count += 1

            # UDP
            elif proto == 17:
                src_port, dest_port, size, data = udp_segment(data)
                print(TAB1 + "UDP Segment:")
                print(TAB2 + 'Source Port: {}, Destination Port: {}'.format(src_port, dest_port))
                udp_count += 1

                if src_port == 80 or dest_port == 80:
                    print(TAB2 + 'HTTP: ')
                    http_count += 1
                elif src_port == 443 or dest_port == 443:
                    print(TAB2 + 'HTTPs: ')
                    https_count += 1
                elif src_port == 25 or dest_port == 25:
                    print(TAB2 + 'SMTP: ')
                elif src_port == 53 or dest_port == 53:
                    print(TAB2 + 'DNS: ')
                    dns_count += 1
                elif (src_port == 20 or src_port == 21) or (dest_port == 20 or dest_port == 21):
                    print(TAB2 + 'FTP: ')

                print(TAB2 + 'Data:')
                print(format_multi_line(DATA_TAB3, data))
                print("-----------------------------------------------------------------------------------------------")

            # Other protocols in transport layer
            else:
                print(TAB1 + "Data:")
                print(format_multi_line(DATA_TAB1, data))
                other_proto += 1
                print("-----------------------------------------------------------------------------------------------")

        # Other protocols in network layer
        else:
            print("Data:")
            print(format_multi_line(DATA_TAB1, data))
            print("---------------------------------------------------------------------------------------------------")

    print("Counters:\n TCP_count: {} UDP_count: {} ICMP_count: {}".format(tcp_count, udp_count, icmp_count))
    counter = (tcp_count, udp_count, icmp_count)

    # print(packet_sent_num)
    list_of_sent_pckts_numb = {}
    a1_sorted_keys = sorted(packet_sent_num, key=packet_sent_num.get, reverse=True)
    for r in a1_sorted_keys:
        list_of_sent_pckts_numb.update({r: packet_sent_num[r]})
    print("Sorted List:\n", list_of_sent_pckts_numb)

    pckts_avg_size, min_size_pckt, max_size_pckt = packets_analyse(data_list)
    print("Sizes\n avg: {} min: {} max: {}".format(pckts_avg_size, min_size_pckt, max_size_pckt))
    packet_analysis = (pckts_avg_size, min_size_pckt, max_size_pckt)

    write_to_file(counter, list_of_sent_pckts_numb, packet_analysis, len(fragmented_dict))
    print("Number of fragmented packets is: " + str(len(fragmented_dict)))
    print("DNS number:{}, HTTP number: {}, HTTPs number {}".format(dns_count, http_count, https_count))


def write_to_file(counter, list_of_sent_pckts_num, packet_analysis, num_of_fragmented_pckts):
    result = open('ReportFile', 'w')
    result.write("TCP exchanged packets number: " + str(counter[0])+"\n")
    result.write("UDP exchanged packets number: "+str(counter[1])+"\n")
    result.write("ICMP exchanged packets number: "+str(counter[2])+"\n")

    for ip in list_of_sent_pckts_num:
        result.write(ip + ": " + str(list_of_sent_pckts_num[ip]) + "\n")

    result.write("Number of fragmented packets is: " + str(num_of_fragmented_pckts) + "\n")

    result.write("Packets average size is: " + str(packet_analysis[0]) + "\n")
    result.write("Minimum size of packets is: " + str(packet_analysis[1]) + "\n")
    result.write("Maximum size of packets is: " + str(packet_analysis[2]) + "\n")
    result.close()


def packets_analyse(data_list):
    pckts_avg = sum(data_list)/len(data_list)
    min_size_pckt = min(data_list)
    max_size_pckt = max(data_list)
    return pckts_avg, min_size_pckt, max_size_pckt


# Unpacks ethernet frame
def ethernet_frame(data):
    dest_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
    return get_mac_address(dest_mac), get_mac_address(src_mac), socket.htons(proto), data[14:]


# Return properly formatted MAC address (ie: AA:BB:CC:DD:EE:FF)
def get_mac_address(bytes_addrr):
    # make proper chunks
    bytes_str = map('{:02x}'.format, bytes_addrr)
    # join chunks together
    mac_addr = ':'.join(bytes_str).upper()
    return mac_addr


# Unpack IPv4 packet
def ipv4_packet(data, fdict):

    global FRAGMENTED_PACKETS_NUM

    version_header_length = data[0]
    d = numpy.fromiter(data[4:8], dtype="uint8")
    identification = d[:2]
    id = identification.dot(2 ** numpy.arange(identification.size)[::-1])

    tmp = numpy.unpackbits(d[2])
    flags = tmp[1:3]
    tmp = numpy.unpackbits(d[2:])
    offset = tmp[3:]

    offset_value = offset.dot(2**numpy.arange(offset.size)[::-1])
    mf_value = flags[1:].dot(2**numpy.arange(flags[1:].size)[::-1])
    df_value = flags[:-1].dot(2 ** numpy.arange(flags[:-1].size)[::-1])

    # print(offset, flags)
    # print(offset_value, mf_value)

    version = version_header_length >> 4
    header_length = (version_header_length & 15) * 4
    ttl, proto, src, target = struct.unpack('! 8x B B 2x 4s 4s', data[:20])

    # if offset_value > 0 or ((mf_value == 1 or df_value == 1) and offset_value == 0):
    #     if (src, target) not in fdict or ((target, src) not in fdict):
    #         fdict.update({(src, target): 0})
    #     else:
    #         if (src, target) in fdict:
    #             fdict[(src, target)] += 1
    #         elif (target, src) in fdict:
    #             fdict[(target, src)] += 1

    if offset_value > 0 or ((mf_value == 1 or df_value == 1) and offset_value == 0):
        if id not in fdict:
            fdict.update({id: 0})
        else:
            if id in fdict:
                fdict[id] += 1

    return version, header_length, ttl, proto, ipv4(src), ipv4(target), data[header_length:], fdict


# Returns properly formatted IPv4 address
def ipv4(addr):
    return '.'.join(map(str, addr))


# Unpacks ICMP packet
def icmp_packet(data):
    icmp_type, code, checksum = struct.unpack('! B B H', data[:4])
    return icmp_type, code, checksum, data[4:]


# Unpacks TCP segment
def tcp_segment(data):
    (src_port, dest_port, sequence, acknowledgement, offset_reserved_flags) = struct.unpack('! H H L L H', data[:14])
    offset = (offset_reserved_flags >> 12) * 4
    flag_urg = (offset_reserved_flags & 32) >> 5
    flag_ack = (offset_reserved_flags & 16) >> 4
    flag_psh = (offset_reserved_flags & 8) >> 3
    flag_rst = (offset_reserved_flags & 4) >> 2
    flag_syn = (offset_reserved_flags & 2) >> 1
    flag_fin = offset_reserved_flags & 1
    return src_port, dest_port, sequence, acknowledgement, flag_urg, flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data[offset:]


# Unpacks UDP segment
def udp_segment(data):
    src_port, dest_port, size = struct.unpack('! H H 2x H', data[:8])
    return src_port, dest_port, size, data[8:]


# Formats multi-line data
def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string, bytes):
        string = ''.join(r'\x{:02x}'.format(byte) for byte in string)
        if size % 2:
            size -= 1
    return '\n'.join([prefix + line for line in textwrap.wrap(string, size)])


def stop_sniffing():
    global EXIT
    while True:
        command = input()
        if command == "stop":
            EXIT = True
            break


if __name__ == '__main__':
    main()
