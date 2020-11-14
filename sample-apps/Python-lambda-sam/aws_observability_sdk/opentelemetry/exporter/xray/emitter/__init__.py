import os
import logging
import socket

from aws_xray_sdk.core.daemon_config import DaemonConfig

log = logging.getLogger(__name__)

DAEMON_ADDRESS_KEY = "AWS_XRAY_DAEMON_ADDRESS"
DEFAULT_ADDRESS = "127.0.0.1:2000"


class DaemonConfig(object):
    """The class that stores X-Ray daemon configuration about
    the ip address and port for UDP and TCP port. It gets the address
    string from ``AWS_TRACING_DAEMON_ADDRESS`` and then from recorder's
    configuration for ``daemon_address``.
    A notation of '127.0.0.1:2000' or 'tcp:127.0.0.1:2000 udp:127.0.0.2:2001'
    are both acceptable. The former one means UDP and TCP are running at
    the same address.
    By default it assumes a X-Ray daemon running at 127.0.0.1:2000
    listening to both UDP and TCP traffic.
    """

    def __init__(self, daemon_address=DEFAULT_ADDRESS):
        if daemon_address is None:
            daemon_address = DEFAULT_ADDRESS

        val = os.getenv(DAEMON_ADDRESS_KEY, daemon_address)
        configs = val.split(" ")
        if len(configs) == 1:
            self._parse_single_form(configs[0])
        elif len(configs) == 2:
            self._parse_double_form(configs[0], configs[1], val)
        else:
            raise InvalidDaemonAddressException(
                "Invalid daemon address %s specified." % val
            )

    def _parse_single_form(self, val):
        try:
            configs = val.split(":")
            self._udp_ip = configs[0]
            self._udp_port = int(configs[1])
            self._tcp_ip = configs[0]
            self._tcp_port = int(configs[1])
        except Exception:
            raise InvalidDaemonAddressException(
                "Invalid daemon address %s specified." % val
            )

    def _parse_double_form(self, val1, val2, origin):
        try:
            configs1 = val1.split(":")
            configs2 = val2.split(":")
            mapping = {
                configs1[0]: configs1,
                configs2[0]: configs2,
            }

            tcp_info = mapping.get("tcp")
            udp_info = mapping.get("udp")

            self._tcp_ip = tcp_info[1]
            self._tcp_port = int(tcp_info[2])
            self._udp_ip = udp_info[1]
            self._udp_port = int(udp_info[2])
        except Exception:
            raise InvalidDaemonAddressException(
                "Invalid daemon address %s specified." % origin
            )

    @property
    def udp_ip(self):
        return self._udp_ip

    @property
    def udp_port(self):
        return self._udp_port

    @property
    def tcp_ip(self):
        return self._tcp_ip

    @property
    def tcp_port(self):
        return self._tcp_port


PROTOCOL_HEADER = '{"format":"json","version":1}'
PROTOCOL_DELIMITER = "\n"
DEFAULT_DAEMON_ADDRESS = "127.0.0.1:2000"


class InvalidDaemonAddressException(Exception):
    pass


class UDPEmitter(object):
    """
    The default emitter the X-Ray recorder uses to send segments/subsegments
    to the X-Ray daemon over UDP using a non-blocking socket. If there is an
    exception on the actual data transfer between the socket and the daemon,
    it logs the exception and continue.
    """

    def __init__(self, daemon_address=DEFAULT_DAEMON_ADDRESS):

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        self.set_daemon_address(daemon_address)

    def send_entity(self, entity):
        """
        Serializes a segment/subsegment and sends it to the X-Ray daemon
        over UDP. By default it doesn't retry on failures.

        :param entity: a trace entity to send to the X-Ray daemon
        """
        # TODO: replace to traslator real data
        message = "%s%s%s" % (PROTOCOL_HEADER, PROTOCOL_DELIMITER, entity)

        log.debug("sending: %s to %s:%s." % (message, self._ip, self._port))
        self._send_data(message)

    def set_daemon_address(self, address):
        """
        Set up UDP ip and port from the raw daemon address
        string using ``DaemonConfig`` class utlities.
        """
        if address:
            daemon_config = DaemonConfig(address)
            self._ip, self._port = daemon_config.udp_ip, daemon_config.udp_port

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def _send_data(self, data):

        try:
            self._socket.sendto(data.encode("utf-8"), (self._ip, self._port))
        except Exception:
            log.exception("failed to send data to X-Ray daemon.")

    def _parse_address(self, daemon_address):
        try:
            val = daemon_address.split(":")
            return val[0], int(val[1])
        except Exception:
            raise InvalidDaemonAddressException(
                "Invalid daemon address %s specified." % daemon_address
            )
